"""Job deduplication.

Real implementation: a job is a duplicate if another job in the same
batch shares the same (source_url) or, when no URL is present, the
same (title, company) pair, case-insensitively. First occurrence wins.
"""

from __future__ import annotations

from typing import Iterable

from incomeos.jobs.models.job import Job


def deduplicate_jobs(jobs: Iterable[Job]) -> list[Job]:
    """Remove duplicate jobs, preserving first-seen order."""
    seen_urls: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    result: list[Job] = []

    for job in jobs:
        url_key = (job.url or job.source_url or "").strip().lower()
        pair_key = ((job.title or "").strip().lower(), (job.company or "").strip().lower())

        if url_key:
            if url_key in seen_urls:
                continue
            seen_urls.add(url_key)
        else:
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

        result.append(job)

    return result