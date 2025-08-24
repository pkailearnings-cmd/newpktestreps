from typing import Tuple
import re


def _strip_html(html: str) -> str:
	# naive HTML tag remover as a fallback
	text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
	text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
	text = re.sub(r"<[^>]+>", " ", text)
	text = re.sub(r"\s+", " ", text)
	return text.strip()


def fetch_job_text(url: str) -> Tuple[str, str]:
	"""Fetch the title and main text of a job posting from a URL.

	Returns (title, text). Title may be empty if not available.
	"""
	try:
		from trafilatura import fetch_url, extract
		from trafilatura.settings import use_config
		cfg = use_config()
		cfg.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")
		downloaded = fetch_url(url)
		if downloaded:
			text = extract(downloaded, config=cfg, include_comments=False, include_tables=False, include_formatting=False)
			if text:
				try:
					from trafilatura.metadata import extract_metadata
					meta = extract_metadata(downloaded, default_url=url)
					title = (meta.title if meta and getattr(meta, 'title', None) else "").strip()
				except Exception:
					title = ""
				return title, text
	except Exception:
		pass

	# Fallback to requests
	try:
		import requests
		resp = requests.get(url, timeout=15)
		resp.raise_for_status()
		title = ""
		if "<title>" in resp.text.lower():
			m = re.search(r"<title>(.*?)</title>", resp.text, re.IGNORECASE | re.DOTALL)
			if m:
				title = m.group(1).strip()
		text = _strip_html(resp.text)
		return title, text
	except Exception:
		return "", ""