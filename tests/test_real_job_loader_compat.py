from pathlib import Path
import sqlite3

from scripts.real_job_pipeline import load_jobs


def test_legacy_job_loader_without_raw_data(tmp_path):
    db = Path(tmp_path) / "jobs.db"

    conn = sqlite3.connect(db)

    try:
        conn.execute(
            """
            CREATE TABLE jobs (
                id INTEGER,
                title TEXT,
                company TEXT,
                url TEXT
            )
            """
        )

        conn.execute(
            """
            INSERT INTO jobs
            VALUES (1, 'Legacy Job', 'Example', 'https://example.com')
            """
        )

        conn.commit()
    finally:
        conn.close()

    jobs = load_jobs(
        db,
        limit=10,
    )

    assert jobs == (
        {
            "id": 1,
            "title": "Legacy Job",
            "company": "Example",
            "url": "https://example.com",
        },
    )


def test_real_job_loader_with_raw_data(tmp_path):
    db = Path(tmp_path) / "jobs.db"

    conn = sqlite3.connect(db)

    try:
        conn.execute(
            """
            CREATE TABLE jobs (
                id INTEGER,
                title TEXT,
                company TEXT,
                url TEXT,
                raw_data TEXT
            )
            """
        )

        conn.execute(
            """
            INSERT INTO jobs
            VALUES (
                1,
                'Python Engineer',
                'Example',
                'https://example.com',
                '{''description'': ''<h2>Required Skills</h2><p>Python SQL</p>''}'
            )
            """
        )

        conn.commit()
    finally:
        conn.close()

    jobs = load_jobs(
        db,
        limit=10,
    )

    assert len(jobs) == 1
    assert jobs[0]["id"] == 1
    assert "raw_data" in jobs[0]
