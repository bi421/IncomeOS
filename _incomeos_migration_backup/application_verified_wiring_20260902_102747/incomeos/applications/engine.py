from __future__ import annotations

import sqlite3
import webbrowser
from datetime import datetime
from pathlib import Path

from incomeos.applications.models import (
    APPLICATION_FAILED,
    APPLICATION_OPENED,
    APPLICATION_PREPARED,
    JobApplication,
)
from incomeos.applications.templates import generate_cover_letter
from incomeos.jobs.integration import get_jobs_by_skill


def _get_applications_db_path(
    data_dir: Path = Path("data"),
) -> Path:
    path = data_dir / "applications.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _init_applications_table(
    data_dir: Path = Path("data"),
) -> None:
    db_path = _get_applications_db_path(data_dir)

    conn = sqlite3.connect(str(db_path))

    try:
        conn.execute(
            """
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
            """
        )
        conn.commit()
    finally:
        conn.close()


def _application_is_prepared(
    job_id: int,
    job_url: str,
    data_dir: Path,
) -> bool:
    _init_applications_table(data_dir)

    db_path = _get_applications_db_path(data_dir)
    conn = sqlite3.connect(str(db_path))

    try:
        row = conn.execute(
            """
            SELECT 1
            FROM applications
            WHERE job_id=?
              AND job_url=?
              AND status IN ('PREPARED', 'OPENED_IN_BROWSER')
            LIMIT 1
            """,
            (job_id, job_url),
        ).fetchone()

        return row is not None
    finally:
        conn.close()


def _save_application(
    app: JobApplication,
    data_dir: Path,
) -> None:
    _init_applications_table(data_dir)

    db_path = _get_applications_db_path(data_dir)
    conn = sqlite3.connect(str(db_path))

    try:
        conn.execute(
            """
            INSERT INTO applications (
                job_id,
                job_title,
                job_url,
                company,
                applied_at,
                status,
                cover_letter_path,
                error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                app.job_id,
                app.job_title,
                app.job_url,
                app.company,
                app.applied_at.isoformat(),
                app.status,
                app.cover_letter_path,
                app.error_message,
            ),
        )

        conn.commit()
    finally:
        conn.close()


def apply_to_jobs(
    skill: str,
    limit: int = 5,
    open_browser: bool = True,
    data_dir: Path = Path("data"),
) -> list[JobApplication]:
    """
    Prepare truthful application artifacts for jobs matching one verified skill.

    This function never claims SUBMITTED.

    PREPARED:
        cover letter/artifact generated but browser not opened.

    OPENED_IN_BROWSER:
        URL was handed to the browser. Human submission remains outside
        IncomeOS.
    """

    jobs = get_jobs_by_skill(
        skill,
        limit=limit,
        db_path=data_dir / "jobs" / "incomeos_jobs.sqlite3",
    )

    if not jobs:
        print(f"No jobs found for skill: {skill}")
        return []

    results: list[JobApplication] = []

    cover_dir = data_dir / "cover_letters"
    cover_dir.mkdir(parents=True, exist_ok=True)

    _init_applications_table(data_dir)

    for job in jobs:
        company = job.get("company", "Unknown")
        title = job.get("title", "N/A")
        url = job.get("url", "")

        if _application_is_prepared(
            job["id"],
            url,
            data_dir,
        ):
            print(
                f"Already prepared: {title} at {company}"
            )
            continue

        filename = (
            cover_dir
            / f"cover_{job['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        cover_text = generate_cover_letter(
            title,
            company,
            [skill],
        )

        filename.write_text(
            cover_text,
            encoding="utf-8",
        )

        status = APPLICATION_PREPARED

        if open_browser and url:
            status = APPLICATION_OPENED
            print(
                f"Opening: {title} at {company}"
            )
        else:
            print(
                f"Prepared: {title} at {company}"
            )
            print(f"URL: {url}")

        if status is APPLICATION_OPENED:
            try:
                webbrowser.open(url)
            except Exception as error:
                status = APPLICATION_FAILED
                error_message = str(error)
            else:
                error_message = None
        else:
            error_message = None

        app = JobApplication(
            job_id=job["id"],
            job_title=title,
            job_url=url,
            company=company,
            applied_at=datetime.now(),
            status=status,
            cover_letter_path=str(filename),
            error_message=error_message,
        )

        _save_application(
            app,
            data_dir,
        )

        results.append(app)

    print(
        f"Prepared {len(results)} applications for skill: {skill}"
    )

    return results


def run_application_pipeline(
    opportunity_name: str,
    required_skills: list[str],
    limit_per_skill: int = 3,
    data_dir: Path = Path("data"),
    open_browser: bool = False,
) -> list[JobApplication]:
    print(
        f"\nPreparing applications for: {opportunity_name}"
    )

    all_apps: list[JobApplication] = []

    for skill in required_skills:
        print(f"\nSkill: {skill}")

        apps = apply_to_jobs(
            skill,
            limit=limit_per_skill,
            open_browser=open_browser,
            data_dir=data_dir,
        )

        all_apps.extend(apps)

    print(
        f"\nTotal {len(all_apps)} applications prepared."
    )

    print(
        "IncomeOS does not claim external submission."
    )

    return all_apps
