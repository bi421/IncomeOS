from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class ApplicationStatus(str, Enum):
    """Human-observed application lifecycle states."""

    SCOUTED = "SCOUTED"
    APPLIED = "APPLIED"
    INTERVIEWING = "INTERVIEWING"
    REJECTED = "REJECTED"
    OFFER = "OFFER"


_ALLOWED_TRANSITIONS = {
    ApplicationStatus.SCOUTED: {
        ApplicationStatus.APPLIED,
        ApplicationStatus.REJECTED,
    },
    ApplicationStatus.APPLIED: {
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.REJECTED,
        ApplicationStatus.OFFER,
    },
    ApplicationStatus.INTERVIEWING: {
        ApplicationStatus.REJECTED,
        ApplicationStatus.OFFER,
    },
    ApplicationStatus.REJECTED: set(),
    ApplicationStatus.OFFER: set(),
}


@dataclass(frozen=True)
class ApplicationRecord:
    """Persisted application tracking record."""

    job_id: str
    title: str
    company: str
    status: ApplicationStatus
    updated_at: str
    evidence_source: str = ""


class ApplicationTracker:
    """Track application state transitions with fail-closed validation."""

    def __init__(self, db_path: str | Path = "data/applications_tracking.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS application_tracking (
                    job_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    evidence_source TEXT NOT NULL
                )"""
            )

    def scout(
        self,
        job_id: str,
        title: str,
        company: str,
        evidence_source: str = "",
    ) -> ApplicationRecord:
        """Create or preserve a SCOUTED record."""
        if not job_id.strip():
            raise ValueError("job_id must not be empty")
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO application_tracking
                   (job_id, title, company, status, updated_at, evidence_source)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    job_id,
                    title,
                    company,
                    ApplicationStatus.SCOUTED.value,
                    now,
                    evidence_source,
                ),
            )
        return self.get(job_id)

    def transition(
        self,
        job_id: str,
        new_status: ApplicationStatus,
        evidence_source: str = "",
    ) -> ApplicationRecord:
        """Transition only along the explicit lifecycle graph."""
        current = self.get(job_id)
        if current is None:
            raise KeyError(f"unknown job_id: {job_id}")
        if new_status not in _ALLOWED_TRANSITIONS[current.status]:
            raise ValueError(
                f"invalid transition {current.status.value} -> {new_status.value}"
            )
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """UPDATE application_tracking
                   SET status=?, updated_at=?, evidence_source=?
                   WHERE job_id=?""",
                (new_status.value, now, evidence_source, job_id),
            )
        return self.get(job_id)

    def get(self, job_id: str) -> ApplicationRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """SELECT job_id, title, company, status, updated_at, evidence_source
                   FROM application_tracking WHERE job_id=?""",
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return ApplicationRecord(
            job_id=row[0],
            title=row[1],
            company=row[2],
            status=ApplicationStatus(row[3]),
            updated_at=row[4],
            evidence_source=row[5],
        )
