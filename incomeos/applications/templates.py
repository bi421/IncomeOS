from datetime import datetime

def generate_cover_letter(job_title: str, company: str, skills: list[str]) -> str:
    """Энгийн хамрах бичгийн загвар (та өөрчлөх боломжтой)"""
    skills_text = ", ".join(skills)
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""
Date: {today}

To the Hiring Team,

I am writing to apply for the position of {job_title} at {company}.

With strong experience in {skills_text}, I am confident I can contribute effectively to your team. My background includes building scalable systems, automation, and data-driven solutions, which align perfectly with the requirements of this role.

I have attached my CV for your review and look forward to the opportunity to discuss how I can add value to {company}.

Sincerely,
IncomeOS Candidate
"""
