from datetime import datetime

def generate_cover_letter(job_title: str, company: str, skills: list[str]) -> str:
    """Бодит, хүн шиг хамрах бичиг (хуурамч мэдээлэлгүй)"""
    skills_text = ", ".join(skills)
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""
Date: {today}

To the Hiring Team,

I am writing to express my interest in the {job_title} position at {company}.

With hands-on experience in {skills_text}, I have built and deployed production-grade systems in both FinTech and AdTech environments. My work includes:
- Backend systems with FastAPI, PostgreSQL, and Redis
- Data pipelines and ETL workflows
- Docker-based deployment and CI/CD
- Building automated job matching and application systems

I am fully remote-ready, comfortable working across time zones, and looking for a stable, long-term role where I can contribute immediately.

You can review my portfolio at: https://github.com/bi421

I look forward to the possibility of contributing to {company}.

Sincerely,
[Your Name Here]
"""
