from typing import List


def _first_line(text: str) -> str:
	for line in text.splitlines():
		line = line.strip()
		if line:
			return line
	return "Target Role"


def generate_tailored_resume(resume_text: str, job_text: str, matched_keywords: List[str]) -> str:
	role_line = _first_line(job_text)[:100]
	skills = sorted(set([kw for kw in matched_keywords if len(kw) > 1]))

	summary = (
		f"Results-driven professional targeting {role_line}. "
		"Proven ability to deliver impact through hands-on execution, cross-functional collaboration, and continuous improvement. "
		"This resume is auto-tailored to highlight relevant experiences and skills for the role."
	)

	skills_section = "\n".join([f"- {s}" for s in skills]) if skills else "- Add role-specific skills and tools here"

	template = f"""
Professional Summary
{summary}

Key Skills & Tools
{skills_section}

Experience & Achievements
{resume_text}
""".strip()

	return template