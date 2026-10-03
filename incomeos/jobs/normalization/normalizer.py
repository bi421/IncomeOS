from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlsplit, urlunsplit

from incomeos.jobs.models.job import Job


def _canonical_url(value: str) -> str:
    parts = urlsplit((value or "").strip())
    if not parts.scheme or not parts.netloc:
        return (value or "").strip()
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, "")
    )


def normalize_job(job: Job | Mapping[str, object]) -> Job:
    """Convert a source mapping or Job into one canonical Job instance.

    Normalization is intentionally loss-minimal: provider-specific fields stay
    in raw_data while the fields consumed by the hunt pipeline are canonical.
    """
    if isinstance(job, Job):
        return Job(
            source=job.source.strip(),
            title=job.title.strip(),
            source_url=_canonical_url(job.source_url),
            company=job.company.strip(),
            description=job.description,
            created_at=job.created_at,
            raw_data=dict(job.raw_data),
        )

    source = str(job.get("source", "") or "").strip()
    title = str(job.get("title", "") or "").strip()
    source_url = _canonical_url(
        str(job.get("source_url", "") or job.get("url", "") or "")
    )
    raw = job.get("raw_data", {})
    raw_data = dict(raw) if isinstance(raw, Mapping) else {"raw_data": raw}
    return Job(
        source=source,
        title=title,
        source_url=source_url,
        company=str(job.get("company", "") or "").strip(),
        description=str(job.get("description", "") or ""),
        created_at=str(job.get("created_at", "") or ""),
        raw_data=raw_data,
    )
