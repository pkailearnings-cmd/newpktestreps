from __future__ import annotations
from datetime import datetime
from typing import Optional
from . import db


class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    mimetype = db.Column(db.String(64), nullable=True)
    original_path = db.Column(db.String(512), nullable=True)
    original_text = db.Column(db.Text, nullable=True)
    parsed_text = db.Column(db.Text, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class JobPosting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(1024), nullable=False)
    title = db.Column(db.String(256), nullable=True)
    text = db.Column(db.Text, nullable=False)
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resume.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("job_posting.id"), nullable=False)
    tailored_text = db.Column(db.Text, nullable=False)
    ats_score = db.Column(db.Float, nullable=False, default=0.0)
    matched_keywords_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    resume = db.relationship("Resume")
    job = db.relationship("JobPosting")