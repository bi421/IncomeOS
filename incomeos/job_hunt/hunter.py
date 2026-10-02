from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit, urlunsplit

from incomeos.jobs.database import JobDatabase
from incomeos.jobs.models.job import Job
from incomeos.jobs.sources.registry import build_sources

from .matcher import match_job
from .models import HuntItem, HuntReport, SourceHealth


class JobSource(Protocol):
    source_name: str

    def fetch(self) -> Iterable[Job]: ...


def _canonical_url(value: str) -> str:
    """Normalize only URL presentation; never alter the source destination."""
    parts = urlsplit(value.strip())
    if not parts.scheme or not parts.netloc:
        return value.strip()
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))


def _job_id(job: Job) -> str:
    return f"{job.source}:{_canonical_url(job.source_url)}"


def _valid(job: Job) -> bool:
    return bool(job.title.strip() and _canonical_url(job.source_url))


class JobHunter:
    """Run a bounded, fail-visible hunt across real public job sources."""

    def __init__(self, data_dir: str | Path = "data") -> None:
        self.data_dir = Path(data_dir)
        self.db = JobDatabase(self.data_dir / "jobs" / "incomeos_jobs.sqlite3")

    def hunt(
        self,
        skills: Sequence[str],
        *,
        sources: Sequence[JobSource] | None = None,
        limit: int = 25,
        minimum_fit: float = 0.0,
    ) -> HuntReport:
        """Fetch, validate, persist, deduplicate, and rank real job postings."""
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if not 0.0 <= minimum_fit <= 1.0:
            raise ValueError("minimum_fit must be between 0 and 1")

        selected = tuple(sources) if sources is not None else tuple(build_sources())
        seen: set[str] = set()
        candidates: list[tuple[Job, float, tuple[str, ...], tuple[str, ...]]] = []
        health: list[SourceHealth] = []

        for source in selected:
            fetched = accepted = 0
            try:
                for job in source.fetch():
                    fetched += 1
                    if not _valid(job):
                        continue
                    key = _job_id(job)
                    if key in seen:
                        continue
                    seen.add(key)
                    accepted += 1
                    score, matched, missing = match_job(job, skills)
                    if score >= minimum_fit:
                        candidates.append((job, score, matched, missing))
                health.append(SourceHealth(source.source_name, fetched, accepted, False))
            except Exception as exc:
                health.append(SourceHealth(source.source_name, fetched, accepted, True, str(exc)))

        rows = []
        for job, score, matched, missing in candidates:
            rows.append({
                "source": job.source,
                "title": job.title,
                "company": job.company,
                "url": _canonical_url(job.source_url),
                "description": job.description,
                "created_at": job.created_at,
                "location": str(job.raw_data.get("location", "")),
                "raw_data": job.raw_data,
            })
        self.db.upsert_many(rows)

        candidates.sort(key=lambda x: (-x[1], x[0].created_at or "", x[0].source_url))
        items = tuple(
            HuntItem(
                job_id=_job_id(job),
                source=job.source,
                title=job.title,
                company=job.company,
                url=_canonical_url(job.source_url),
                location=str(job.raw_data.get("location", "")),
                fit_score=score,
                matched_skills=matched,
                missing_skills=missing,
            )
            for job, score, matched, missing in candidates[:limit]
        )
        return HuntReport(items=items, sources=tuple(health))
