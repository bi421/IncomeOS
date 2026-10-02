from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from datetime import datetime, timezone

from incomeos.applications.generator import EvidenceBoundGenerator, GeneratedApplication
from incomeos.jobs.models.job import Job
from incomeos.tracking.tracker import ApplicationTracker
from .eligibility import EligibilityResult


@dataclass(frozen=True)
class PreparedApplication:
    job_id: str
    title: str
    company: str
    url: str
    fit_score: float
    eligibility: EligibilityResult
    application: GeneratedApplication
    status: str


class ApplicationQueue:
    """Persist application-ready packages; submission remains human-controlled."""

    def __init__(self, db_path: str | Path = "data/application_queue.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS application_queue (
                    job_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    url TEXT NOT NULL,
                    fit_score REAL NOT NULL,
                    eligibility_status TEXT NOT NULL,
                    eligibility_reason TEXT NOT NULL,
                    package_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )

    def prepare(
        self,
        *,
        job: Job,
        fit_score: float,
        eligibility: EligibilityResult,
        generator: EvidenceBoundGenerator,
        tracker: ApplicationTracker | None = None,
    ) -> PreparedApplication | None:
        if not 0.0 <= fit_score <= 1.0:
            raise ValueError("fit_score must be between 0 and 1")
        if eligibility.status != "PASS":
            return None
        if not job.source_url.strip() or not job.title.strip():
            raise ValueError("job must have title and source_url")

        package = generator.generate(job.description)
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "claim_ids": list(package.claim_ids),
            "cover_letter": package.cover_letter,
            "resume_summary": package.resume_summary,
        }
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO application_queue
                   (job_id,title,company,url,fit_score,eligibility_status,
                    eligibility_reason,package_json,status,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(job_id) DO UPDATE SET
                     fit_score=excluded.fit_score,
                     eligibility_status=excluded.eligibility_status,
                     eligibility_reason=excluded.eligibility_reason,
                     package_json=excluded.package_json,
                     status='READY',
                     updated_at=excluded.updated_at""",
                (
                    job.source_url,
                    job.title,
                    job.company,
                    job.source_url,
                    fit_score,
                    eligibility.status,
                    eligibility.reason,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    "READY",
                    now,
                ),
            )
        if tracker is not None:
            tracker.scout(job.source_url, job.title, job.company, "IncomeOS application-ready queue")
        return PreparedApplication(
            job_id=job.source_url,
            title=job.title,
            company=job.company,
            url=job.source_url,
            fit_score=fit_score,
            eligibility=eligibility,
            application=package,
            status="READY",
        )

    def approve(self, job_id: str, tracker: ApplicationTracker | None = None) -> PreparedApplication:
        row = self._get_row(job_id)
        if row is None:
            raise KeyError(f"unknown queued job_id: {job_id}")
        if row[8] != "READY":
            raise ValueError(f"application is not READY: {row[8]}")
        with self._connect() as conn:
            conn.execute(
                "UPDATE application_queue SET status='APPROVED', updated_at=? WHERE job_id=?",
                (datetime.now(timezone.utc).isoformat(), job_id),
            )
        if tracker is not None:
            tracker.scout(job_id, row[1], row[2], "human approved application package")
        payload = json.loads(row[7])
        application = GeneratedApplication(
            cover_letter=payload["cover_letter"],
            resume_summary=payload["resume_summary"],
            claim_ids=tuple(payload["claim_ids"]),
            prompt="",
        )
        return PreparedApplication(
            job_id=row[0], title=row[1], company=row[2], url=row[3],
            fit_score=float(row[4]),
            eligibility=EligibilityResult(row[5], row[6], None, ""),
            application=application,
            status="APPROVED",
        )

    def _get_row(self, job_id: str):
        with self._connect() as conn:
            return conn.execute(
                "SELECT job_id,title,company,url,fit_score,eligibility_status,eligibility_reason,package_json,status,updated_at FROM application_queue WHERE job_id=?",
                (job_id,),
            ).fetchone()

    def status(self, job_id: str) -> str | None:
        row = self._get_row(job_id)
        return None if row is None else str(row[8])
