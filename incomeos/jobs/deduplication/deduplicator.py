from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlsplit, urlunsplit

from incomeos.jobs.models.job import Job


def _canonical_url(value: str) -> str:
    parts = urlsplit((value or "").strip())
    if not parts.scheme or not parts.netloc:
        return (value or "").strip()
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, "")
    )


def deduplicate_jobs(jobs: Iterable[Job]) -> list[Job]:
    """Keep the first job for each canonical source URL."""
    result: list[Job] = []
    seen: set[str] = set()
    for job in jobs:
        key = _canonical_url(job.source_url or job.url)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(job)
    return result
