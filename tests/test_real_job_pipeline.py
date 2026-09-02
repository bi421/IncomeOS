
import sqlite3
from pathlib import Path

from scripts.real_job_pipeline import (
    discover_job_table,
    load_jobs,
)


def create_job_db(path: Path) -> None:
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

        conn.execute(
            """
            INSERT INTO jobs (
                id,
                title,
                company,
                url
            )
            VALUES (
                2,
                'Automation Engineer',
                'Example Two',
                'https://example.test/2'
            )
            """
        )

        conn.commit()

    finally:
        conn.close()


def test_real_job_table_discovery(tmp_path):
    db = tmp_path / "jobs.db"

    create_job_db(db)

    table, columns = discover_job_table(
        db
    )

    assert table == "jobs"
    assert "id" in columns
    assert "title" in columns
    assert "company" in columns
    assert "url" in columns


def test_real_job_loader(tmp_path):
    db = tmp_path / "jobs.db"

    create_job_db(db)

    jobs = load_jobs(
        db,
        limit=10,
    )

    assert len(jobs) == 2

    assert jobs[0]["id"] == 1
    assert jobs[0]["title"] == "Python Engineer"
    assert jobs[0]["company"] == "Example"
    assert jobs[0]["url"] == "https://example.test/1"
