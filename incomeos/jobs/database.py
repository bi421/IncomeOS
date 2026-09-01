import sqlite3
from pathlib import Path
from typing import Any

class JobDatabase:
    def __init__(self, path: Path):
        self.path = path
        self._init_db()

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    title TEXT,
                    url TEXT UNIQUE,
                    created_at TEXT,
                    raw_data TEXT
                )
            """)

    def _connect(self):
        return sqlite3.connect(str(self.path))

    def upsert_many(self, jobs: list[dict[str, Any]]) -> tuple[int, int]:
        if not jobs:
            return 0, 0

        inserted = 0
        existing = 0
        conn = sqlite3.connect(str(self.path))
        try:
            conn.execute("BEGIN TRANSACTION")
            for job in jobs:
                cur = conn.execute("SELECT id FROM jobs WHERE url = ?", (job["url"],))
                if cur.fetchone():
                    existing += 1
                    continue
                conn.execute(
                    "INSERT INTO jobs (source, title, url, created_at, raw_data) VALUES (?, ?, ?, ?, ?)",
                    (
                        job.get("source", ""),
                        job.get("title", ""),
                        job["url"],
                        job.get("created_at", ""),
                        str(job),
                    )
                )
                inserted += 1
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return inserted, existing