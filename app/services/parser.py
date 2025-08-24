import os
from typing import Optional


def _normalize_text(text: str) -> str:
	text = text.replace("\r\n", "\n").replace("\r", "\n")
	lines = [line.strip() for line in text.split("\n")]
	normalized_lines = []
	blank_count = 0
	for line in lines:
		if line == "":
			blank_count += 1
			if blank_count > 1:
				continue
		else:
			blank_count = 0
		normalized_lines.append(line)
	return "\n".join(normalized_lines).strip()


def _parse_pdf(path: str) -> str:
	try:
		from pypdf import PdfReader
		reader = PdfReader(path)
		texts = []
		for page in reader.pages:
			try:
				texts.append(page.extract_text() or "")
			except Exception:
				continue
		return _normalize_text("\n".join(texts))
	except Exception:
		return ""


def _parse_docx(path: str) -> str:
	try:
		from docx import Document
		doc = Document(path)
		paras = [p.text for p in doc.paragraphs]
		return _normalize_text("\n".join([p for p in paras if p]))
	except Exception:
		return ""


def _parse_txt(path: str) -> str:
	try:
		with open(path, "r", encoding="utf-8", errors="ignore") as f:
			return _normalize_text(f.read())
	except Exception:
		return ""


def parse_resume_file(path: str) -> str:
	"""Parse resume text content from a file path.

	Supports PDF, DOCX, and TXT. Returns normalized plaintext.
	"""
	ext = os.path.splitext(path)[1].lower()
	if ext == ".pdf":
		text = _parse_pdf(path)
	elif ext == ".docx":
		text = _parse_docx(path)
	elif ext == ".txt":
		text = _parse_txt(path)
	else:
		text = ""

	if not text:
		# Fallback: read raw bytes as text best-effort
		try:
			with open(path, "rb") as f:
				data = f.read()
			text = _normalize_text(data.decode("utf-8", errors="ignore"))
		except Exception:
			text = ""
	return text