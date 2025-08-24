from __future__ import annotations
import re
from collections import Counter
from typing import Dict, List, Tuple

_STOPWORDS = {
	"a", "an", "the", "and", "or", "of", "to", "in", "for", "on", "with", "by", "as", "at", "from",
	"is", "are", "was", "were", "be", "being", "been", "that", "this", "it", "its", "if", "not",
	"can", "will", "would", "should", "could", "may", "might", "have", "has", "had", "do", "does", "did",
	"your", "you", "we", "our", "they", "their", "them", "i", "he", "she", "his", "her", "us",
	"job", "role", "responsibilities", "requirements", "qualifications", "about", "company", "years"
}

_SKILL_KEYWORDS = {
	# General
	"python", "java", "javascript", "typescript", "golang", "go", "ruby", "php", "c#", "c++",
	"node", "node.js", "nodejs", "react", "react.js", "reactjs", "vue", "angular", "svelte",
	"django", "flask", "fastapi", "spring", "spring boot", "rails", "laravel", "express",
	"sql", "postgres", "mysql", "oracle", "mongodb", "redis", "dynamodb", "elasticsearch",
	"kubernetes", "docker", "terraform", "ansible", "jenkins", "github actions", "gitlab ci",
	"aws", "azure", "gcp", "s3", "ec2", "lambda", "cloudformation", "gke", "eks", "aks",
	"pandas", "numpy", "scikit-learn", "sklearn", "pytorch", "tensorflow", "mlops", "data pipeline",
	"graphql", "rest", "grpc", "microservices", "event-driven", "kafka", "rabbitmq",
	"ci/cd", "continuous integration", "continuous delivery", "agile", "scrum",
	"linux", "bash", "shell", "testing", "pytest", "jest", "cypress", "playwright",
	"html", "css", "sass", "less", "tailwind", "bootstrap",
	"seo", "analytics", "product management", "project management", "jira",
}


def _normalize(text: str) -> str:
	return re.sub(r"\s+", " ", text.lower()).strip()


def _tokenize(text: str) -> List[str]:
	return re.findall(r"[a-zA-Z0-9+#.]+", text.lower())


def _bigrams(tokens: List[str]) -> List[str]:
	return [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]


def _extract_job_keywords(job_text: str, max_keywords: int = 60) -> List[str]:
	tokens = _tokenize(job_text)
	tokens = [t for t in tokens if t not in _STOPWORDS]
	counts = Counter(tokens)

	bigrams = _bigrams(tokens)
	bigram_counts = Counter([b for b in bigrams if not any(w in _STOPWORDS for w in b.split())])

	skills_in_jd = [s for s in _SKILL_KEYWORDS if s in job_text.lower()]

	top_tokens = [t for t, _ in counts.most_common(40)]
	top_bigrams = [b for b, _ in bigram_counts.most_common(30)]

	combined: List[str] = []
	for item in skills_in_jd + top_bigrams + top_tokens:
		if item not in combined and len(item) > 1:
			combined.append(item)
			if len(combined) >= max_keywords:
				break
	return combined


def _contains_phrase(text: str, phrase: str) -> bool:
	if " " in phrase:
		return phrase in text
	return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def score_resume_against_job(resume_text: str, job_text: str) -> Dict[str, object]:
	resume_norm = _normalize(resume_text)
	job_norm = _normalize(job_text)

	job_keywords = _extract_job_keywords(job_norm)

	matched: List[str] = []
	missing: List[str] = []
	for kw in job_keywords:
		if _contains_phrase(resume_norm, kw):
			matched.append(kw)
		else:
			missing.append(kw)

	total = max(len(job_keywords), 1)
	match_ratio = len(matched) / total
	score = round(match_ratio * 100.0, 1)

	return {
		"score": score,
		"matched_keywords": matched,
		"missing_keywords": missing,
		"job_keywords": job_keywords,
	}