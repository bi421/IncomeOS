"""SQLite storage for real discovered jobs."""

import sqlite3
from pathlib import Path
from typing import Iterable

from incomeos.jobs.models.job import Job


DEFAULT_DB = Path("data/jobs/incomeos_jobs.sqlite3")


class JobDatabase:
    """Persistent local storage for canonical jobs."""

    def __init__(self, path: Path = DEFAULT_DB) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT,
                    description TEXT NOT NULL,
                    source TEXT NOT NULL,
                    source_url TEXT NOT NULL UNIQUE,
                    posted_at TEXT,
                    location TEXT,
                    employment_type TEXT,
                    compensation TEXT,
                    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_jobs_source
                ON jobs(source)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_jobs_title
                ON jobs(title)
                """
            )

    def upsert(self, job: Job) -> bool:
        """Insert a job if its source URL is not already stored.

        Returns True when a new record was inserted.
        """

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO jobs (
                    title,
                    company,
                    description,
                    source,
                    source_url,
                    posted_at,
                    location,
                    employment_type,
                    compensation
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.title,
                    job.company,
                    job.description,
                    job.source,
                    job.source_url,
                    job.posted_at,
                    job.location,
                    job.employment_type,
                    job.compensation,
                ),
            )

            if cursor.rowcount == 1:
                return True

            connection.execute(
                """
                UPDATE jobs
                SET last_seen_at = CURRENT_TIMESTAMP
                WHERE source_url = ?
                """,
                (job.source_url,),
            )

            return False

    def upsert_many(self, jobs: Iterable[Job]) -> tuple[int, int]:
        """Store jobs and return (inserted, existing)."""

        inserted = 0
        existing = 0

        for job in jobs:
            if not job.source_url:
                continue

            if self.upsert(job):
                inserted += 1
            else:
                existing += 1

        return inserted, existing

    def count(self) -> int:
        """Return total stored job count."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM jobs"
            ).fetchone()

        return int(row[0])

    def count_by_source(self) -> dict[str, int]:
        """Return stored job counts grouped by source."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT source, COUNT(*)
                FROM jobs
                GROUP BY source
                ORDER BY source
                """
            ).fetchall()

        return {
            str(source): int(count)
            for source, count in rows
        }
