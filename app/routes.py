import io
import json
import os
from typing import Dict, Any
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename

from . import db
from .models import Resume, JobPosting, Analysis
from .services.parser import parse_resume_file
from .services.job_fetcher import fetch_job_text
from .services.ats import score_resume_against_job
from .services.tailor import generate_tailored_resume


ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def index():
    resumes = Resume.query.order_by(Resume.uploaded_at.desc()).all()
    return render_template("index.html", resumes=resumes)


@main_bp.route("/upload", methods=["POST"])
def upload_resume():
    file = request.files.get("resume_file")
    if file is None or file.filename == "":
        flash("No file selected", "error")
        return redirect(url_for("main.index"))

    if not _allowed_file(file.filename):
        flash("Unsupported file type. Use PDF, DOCX, or TXT.", "error")
        return redirect(url_for("main.index"))

    filename = secure_filename(file.filename)
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

    # Avoid overwriting existing files by appending a counter
    base, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(save_path):
        filename = f"{base}_{counter}{ext}"
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        counter += 1

    file.save(save_path)
    parsed_text = parse_resume_file(save_path)

    resume = Resume(
        filename=filename,
        mimetype=file.mimetype,
        original_path=save_path,
        original_text=None,
        parsed_text=parsed_text,
    )
    db.session.add(resume)
    db.session.commit()

    flash("Resume uploaded and parsed successfully.", "success")
    return redirect(url_for("main.index"))


@main_bp.route("/analyze", methods=["POST"])
def analyze():
    resume_id = request.form.get("resume_id")
    job_url = request.form.get("job_url", "").strip()

    if not resume_id or not job_url:
        flash("Please select a resume and enter a job URL.", "error")
        return redirect(url_for("main.index"))

    resume = Resume.query.get(int(resume_id))
    if resume is None:
        flash("Selected resume not found.", "error")
        return redirect(url_for("main.index"))

    # Fetch or reuse job posting
    job = JobPosting.query.filter_by(url=job_url).first()
    if job is None:
        job_title, job_text = fetch_job_text(job_url)
        if not job_text or len(job_text.strip()) == 0:
            flash("Could not extract content from job URL. Please verify the link.", "error")
            return redirect(url_for("main.index"))
        job = JobPosting(url=job_url, title=job_title, text=job_text)
        db.session.add(job)
        db.session.commit()

    scoring = score_resume_against_job(resume.parsed_text, job.text)
    tailored = generate_tailored_resume(resume.parsed_text, job.text, scoring.get("matched_keywords", []))

    analysis = Analysis(
        resume_id=resume.id,
        job_id=job.id,
        tailored_text=tailored,
        ats_score=float(scoring.get("score", 0.0)),
        matched_keywords_json=json.dumps({
            "matched": scoring.get("matched_keywords", []),
            "missing": scoring.get("missing_keywords", []),
            "job_keywords": scoring.get("job_keywords", []),
        }),
    )
    db.session.add(analysis)
    db.session.commit()

    return redirect(url_for("main.editor", analysis_id=analysis.id))


@main_bp.route("/editor/<int:analysis_id>", methods=["GET"])
def editor(analysis_id: int):
    analysis = Analysis.query.get_or_404(analysis_id)
    job = JobPosting.query.get_or_404(analysis.job_id)
    scoring = score_resume_against_job(analysis.tailored_text, job.text)
    return render_template(
        "editor.html",
        analysis=analysis,
        job=job,
        scoring=scoring,
    )


@main_bp.route("/api/recalc", methods=["POST"])
def api_recalc():
    data: Dict[str, Any] = request.get_json(force=True)
    resume_text = data.get("resume_text", "")
    job_text = data.get("job_text", "")
    if not resume_text or not job_text:
        return {"error": "resume_text and job_text are required"}, 400

    scoring = score_resume_against_job(resume_text, job_text)
    return scoring, 200


@main_bp.route("/save_draft", methods=["POST"])
def save_draft():
    analysis_id = int(request.form.get("analysis_id", "0"))
    tailored_text = request.form.get("tailored_text", "")

    analysis = Analysis.query.get_or_404(analysis_id)
    job = JobPosting.query.get_or_404(analysis.job_id)

    analysis.tailored_text = tailored_text
    scoring = score_resume_against_job(tailored_text, job.text)
    analysis.ats_score = float(scoring.get("score", 0.0))
    analysis.matched_keywords_json = json.dumps({
        "matched": scoring.get("matched_keywords", []),
        "missing": scoring.get("missing_keywords", []),
        "job_keywords": scoring.get("job_keywords", []),
    })

    db.session.commit()
    flash("Draft saved and ATS score updated.", "success")
    return redirect(url_for("main.editor", analysis_id=analysis.id))


@main_bp.route("/download/<int:analysis_id>", methods=["GET"])
def download_docx(analysis_id: int):
    analysis = Analysis.query.get_or_404(analysis_id)

    try:
        from docx import Document
    except Exception:  # pragma: no cover
        flash("python-docx is not installed.", "error")
        return redirect(url_for("main.editor", analysis_id=analysis.id))

    document = Document()
    for line in analysis.tailored_text.splitlines():
        document.add_paragraph(line)

    memfile = io.BytesIO()
    document.save(memfile)
    memfile.seek(0)

    download_name = f"tailored_resume_{analysis.id}.docx"
    return send_file(
        memfile,
        as_attachment=True,
        download_name=download_name,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )