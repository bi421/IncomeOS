from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class JobDatabase:
    def __init__(self, path: Path):
        self.path = path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(str(self.path))

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL DEFAULT '',
                    url TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT '',
                    location TEXT NOT NULL DEFAULT '',
                    raw_data TEXT NOT NULL DEFAULT '',
                    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            columns = {row[1] for row in conn.execute("PRAGMA table_info(jobs)")}
            migrations = {
                "company": "TEXT NOT NULL DEFAULT ''",
                "description": "TEXT NOT NULL DEFAULT ''",
                "location": "TEXT NOT NULL DEFAULT ''",
                "first_seen_at": "TEXT NOT NULL DEFAULT ''",
                "last_seen_at": "TEXT NOT NULL DEFAULT ''",
            }
            for column, definition in migrations.items():
                if column not in columns:
                    conn.execute(f"ALTER TABLE jobs ADD COLUMN {column} {definition}")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title)")

    def upsert_many(self, jobs: list[dict[str, Any]]) -> tuple[int, int]:
        if not jobs:
            return 0, 0
        inserted = 0
        existing = 0
        with self._connect() as conn:
            conn.execute("BEGIN")
            for job in jobs:
                url = str(job.get("url") or job.get("source_url") or "").strip()
                if not url:
                    continue
                cur = conn.execute("SELECT id FROM jobs WHERE url = ?", (url,))
                if cur.fetchone():
                    existing += 1
                    conn.execute(
                        "UPDATE jobs SET last_seen_at=CURRENT_TIMESTAMP WHERE url=?",
                        (url,),
                    )
                    continue
                conn.execute(
                    """
                    INSERT INTO jobs
                    (source, title, company, url, description, created_at, location, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.get("source", ""),
                        job.get("title", ""),
                        job.get("company", ""),
                        url,
                        job.get("description", ""),
                        job.get("created_at", ""),
                        job.get("location", ""),
                        str(job.get("raw_data", job)),
                    ),
                )
                inserted += 1
        return inserted, existing

    def count(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0])

    def count_by_source(self) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute("SELECT source, COUNT(*) FROM jobs GROUP BY source ORDER BY source").fetchall()
        return {str(source): int(count) for source, count in rows}
