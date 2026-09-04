"""Job ingestion orchestration.

Real implementation: fetches from every registered real source adapter
(currently arbeitnow, remoteok, weworkremotely - LinkedIn scraping was
removed, see incomeos/jobs/sources/registry.py), normalizes, and
deduplicates. Any single source failing (network error, API change)
does not take down the whole run - it's logged and skipped.
"""

from __future__ import annotations

from incomeos.jobs.deduplication.deduplicator import deduplicate_jobs
from incomeos.jobs.models.job import Job
from incomeos.jobs.normalization.normalizer import normalize_job
from incomeos.jobs.sources.registry import build_sources


def collect_jobs() -> list[Job]:
    """Collect jobs from every configured source adapter."""
    raw_jobs: list[Job] = []

    for source in build_sources():
        try:
            fetched = list(source.fetch())
        except Exception as exc:  # network/API failures should not kill the run
            print(f"[ingestion] {source.source_name} fetch failed: {exc}")
            continue
        raw_jobs.extend(fetched)

    normalized = [normalize_job(job) for job in raw_jobs]
    return deduplicate_jobs(normalized)