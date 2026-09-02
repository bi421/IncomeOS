
from pathlib import Path
import sqlite3

from incomeos.decision.job_decision import discover_job_table, load_jobs


def create_job_db(path: Path):
    conn = sqlite3.connect(path)

    try:
        conn.execute(
            """
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                company TEXT,
                url TEXT
            )
            """
        )

        conn.execute(
            """
            INSERT INTO jobs (
                id,
                title,
                company,
                url
            )
            VALUES (
                1,
                'Python Engineer',
                'Example',
                'https://example.test/1'
            )
            """
        )

        conn.commit()
    finally:
        conn.close()


def test_real_job_table_discovery(tmp_path):
    db = tmp_path / "jobs.db"

    create_job_db(db)

    table, columns = discover_job_table(db)

    assert table == "jobs"
    assert "id" in columns
    assert "title" in columns


def test_real_job_loader(tmp_path):
    db = tmp_path / "jobs.db"

    create_job_db(db)

    jobs = load_jobs(
        db,
        limit=10,
    )

    assert len(jobs) == 1
    assert jobs[0]["id"] == 1
    assert jobs[0]["title"] == "Python Engineer"
    assert jobs[0]["company"] == "Example"
