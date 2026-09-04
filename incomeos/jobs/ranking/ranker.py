"""Opportunity ranking.

Real implementation: ranks (job, MatchResult) pairs by match score,
descending. Ties break by verification status (verified jobs first),
then by title for determinism.
"""

from __future__ import annotations

from typing import Iterable

from incomeos.jobs.matching.matcher import MatchResult
from incomeos.jobs.models.job import Job
from incomeos.jobs.verification.verifier import verify_job


def rank_jobs(scored_jobs: Iterable[tuple[Job, MatchResult]]) -> list[tuple[Job, MatchResult]]:
    """Rank (job, match_result) pairs by score, verified jobs breaking ties."""
    items = list(scored_jobs)
    return sorted(
        items,
        key=lambda pair: (pair[1].score, verify_job(pair[0]), pair[0].title.lower()),
        reverse=True,
    )