"""Canonical job normalization.

Real implementation: trims whitespace, fills required fields with safe
defaults, truncates oversized descriptions, and lower-cases the source
tag so downstream dedup/matching can rely on consistent fields.
"""

from __future__ import annotations

from incomeos.jobs.models.job import Job

_MAX_DESCRIPTION_CHARS = 4000


def normalize_job(job: Job) -> Job:
    """Normalize an external job into canonical representation."""
    title = (job.title or "Untitled").strip()
    company = (job.company or "Unknown").strip()
    description = (job.description or "").strip()[:_MAX_DESCRIPTION_CHARS]
    source = (job.source or "unknown").strip().lower()
    url = (job.url or job.source_url or "").strip()

    return Job(
        source=source,
        title=title,
        source_url=url,
        company=company,
        description=description,
        created_at=job.created_at,
        raw_data=job.raw_data,
        url=url,
    )