import sqlite3
from pathlib import Path
from typing import Any, Iterable
from incomeos.jobs.models.job import Job

class JobDatabase:
    def __init__(self, path: Path):
        self.path = path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.path))
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    title TEXT,
                    url TEXT UNIQUE,
                    source_url TEXT,
                    company TEXT,
                    description TEXT,
                    created_at TEXT,
                    raw_data TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def upsert_many(self, jobs: Iterable[Job]) -> tuple[int, int]:
        inserted = 0
        existing = 0
        conn = sqlite3.connect(str(self.path))
        try:
            conn.execute("BEGIN TRANSACTION")
            for job in jobs:
                cur = conn.execute("SELECT id FROM jobs WHERE url = ?", (job.url,))
                if cur.fetchone():
                    existing += 1
                    continue
                conn.execute(
                    "INSERT INTO jobs (source, title, url, source_url, company, description, created_at, raw_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (job.source, job.title, job.url, job.source_url, job.company, job.description, job.created_at, str(job.raw_data))
                )
                inserted += 1
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return inserted, existing
