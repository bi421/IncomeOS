from __future__ import annotations
import sqlite3
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Optional

from incomeos.jobs.integration import get_jobs_by_skill
from incomeos.applications.templates import generate_cover_letter
from incomeos.applications.models import JobApplication

def _get_applications_db_path(data_dir: Path = Path("data")) -> Path:
    path = data_dir / "applications.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def _init_applications_table():
    db_path = _get_applications_db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                job_title TEXT,
                job_url TEXT,
                company TEXT,
                applied_at TEXT,
                status TEXT,
                cover_letter_path TEXT,
                error_message TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()

def _save_application(app: JobApplication):
    _init_applications_table()
    db_path = _get_applications_db_path()
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("""
            INSERT INTO applications (job_id, job_title, job_url, company, applied_at, status, cover_letter_path, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (app.job_id, app.job_title, app.job_url, app.company, app.applied_at.isoformat(), app.status, app.cover_letter_path, app.error_message))
        conn.commit()
    finally:
        conn.close()

def apply_to_jobs(skill: str, limit: int = 5, open_browser: bool = True, data_dir: Path = Path("data")) -> list[JobApplication]:
    jobs = get_jobs_by_skill(skill, limit=limit, db_path=data_dir / "jobs" / "incomeos_jobs.sqlite3")
    if not jobs:
        print(f"⚠️ No jobs found for skill: {skill}")
        return []

    results: list[JobApplication] = []
    cover_dir = data_dir / "cover_letters"
    cover_dir.mkdir(parents=True, exist_ok=True)

    for idx, job in enumerate(jobs):
        company = job.get('company', 'Unknown')
        title = job.get('title', 'N/A')
        url = job.get('url', '')
        
        # 1. Хамрах бичиг
        filename = cover_dir / f"cover_{job['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        cover_text = generate_cover_letter(title, company, [skill])
        filename.write_text(cover_text, encoding="utf-8")

        # 2. Лог
        app = JobApplication(
            job_id=job['id'],
            job_title=title,
            job_url=url,
            company=company,
            applied_at=datetime.now(),
            status="PENDING",
            cover_letter_path=str(filename)
        )

        # 3. Хөтөч нээх
        if open_browser and url:
            print(f"🌐 Opening URL: {url}")
            webbrowser.open(url)
            app.status = "SUBMITTED"
        else:
            print(f"📄 Application ready for: {title} at {company}")
            print(f"   URL: {url}")

        _save_application(app)
        results.append(app)

    print(f"\n✅ Processed {len(results)} applications for skill: {skill}")
    return results

def run_application_pipeline(opportunity_name: str, required_skills: list[str], limit_per_skill: int = 3):
    print(f"\n🚀 Starting application pipeline for: {opportunity_name}")
    all_apps = []
    for skill in required_skills:
        print(f"\n📌 Applying with skill: {skill}")
        apps = apply_to_jobs(skill, limit=limit_per_skill, open_browser=False)
        all_apps.extend(apps)
    print(f"\n✅ Done. Total {len(all_apps)} applications generated.")
    return all_apps
