from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from incomeos.job_hunt.eligibility import assess_eligibility
from incomeos.jobs.database import JobDatabase
from incomeos.jobs.models.job import Job
from incomeos.jobs.sources.registry import build_sources

from .matcher import match_job
from .models import HuntItem, HuntReport, SourceHealth
from .source_evidence import descriptor_for, observed_now
from .scoring import score_job

_TRACKING_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "referrer", "source",
}


class JobSource(Protocol):
    source_name: str
    def fetch(self) -> Iterable[Job]: ...


def _canonical_url(value: str) -> str:
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        return ""
    query = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in _TRACKING_KEYS and not k.lower().startswith("utm_")
    ]
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(),
         parts.path.rstrip("/") or "/", urlencode(query), "")
    )


def _job_id(job: Job) -> str:
    return _canonical_url(job.source_url)


def _valid(job: Job) -> bool:
    return bool(job.title.strip() and _canonical_url(job.source_url))


def _display_location(job: Job) -> str:
    raw = job.raw_data if isinstance(job.raw_data, dict) else {}
    values: list[str] = []
    for key in (
        "location", "candidate_required_location", "candidate_location",
        "job_location", "country", "region", "state",
    ):
        value = raw.get(key)
        if value is not None and str(value).strip():
            values.append(str(value).strip())
    restrictions = raw.get("locationRestrictions")
    if isinstance(restrictions, (list, tuple, set)):
        values.extend(str(x).strip() for x in restrictions if str(x).strip())
    return " | ".join(dict.fromkeys(values))


def _job_check_score(
    job: Job,
    matched: tuple[str, ...],
    requested_skill_count: int,
    eligibility_reason: str,
):
    return score_job(
        job,
        matched_skills=matched,
        requested_skill_count=requested_skill_count,
        eligibility_reason=eligibility_reason,
    )


class JobHunter:
    """Fail-closed real-job hunt: valid URL + skill match + location eligibility."""

    def __init__(self, data_dir: str | Path = "data") -> None:
        self.data_dir = Path(data_dir)
        db_path = self.data_dir / "jobs" / "incomeos_jobs.sqlite3"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = JobDatabase(db_path)

    def hunt(
        self,
        skills: Sequence[str],
        *,
        sources: Sequence[JobSource] | None = None,
        limit: int = 25,
        minimum_fit: float = 0.0,
        target_country: str = "Mongolia",
    ) -> HuntReport:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if not 0.0 <= minimum_fit <= 1.0:
            raise ValueError("minimum_fit must be between 0 and 1")
        if not target_country.strip():
            raise ValueError("target_country must not be empty")

        selected = tuple(sources) if sources is not None else tuple(build_sources())
        unique_skills = tuple(dict.fromkeys(s.strip() for s in skills if s.strip()))
        if not unique_skills:
            raise ValueError("at least one non-empty skill is required")

        seen: set[str] = set()
        candidates = []
        health: list[SourceHealth] = []

        for source in selected:
            fetched = accepted = 0
            descriptor = descriptor_for(source.source_name)
            observed_at = observed_now()
            try:
                for job in source.fetch():
                    fetched += 1
                    if not _valid(job):
                        continue
                    key = _job_id(job)
                    if key in seen:
                        continue
                    seen.add(key)

                    score, matched, missing = match_job(job, unique_skills)
                    # minimum_fit=0 must never mean "accept unrelated jobs".
                    if not matched or score < minimum_fit:
                        continue

                    eligibility = assess_eligibility(job, target_country)
                    # UNKNOWN is deliberately excluded from the user-facing
                    # result: absence of location evidence is not proof of
                    # Mongolia eligibility.
                    if eligibility.status != "PASS":
                        continue

                    accepted += 1
                    candidates.append(
                        (job, score, matched, missing,
                         eligibility.status, eligibility.reason)
                    )

                health.append(
                    SourceHealth(
                        source.source_name, fetched, accepted, False,
                        endpoint=descriptor.endpoint,
                        protocol=descriptor.protocol,
                        provider_type=descriptor.provider_type,
                        observed_at=observed_at,
                    )
                )
            except Exception as exc:
                health.append(
                    SourceHealth(
                        source.source_name, fetched, accepted, True, str(exc),
                        descriptor.endpoint, descriptor.protocol,
                        descriptor.provider_type, observed_at,
                    )
                )

        rows = []
        for job, score, matched, missing, _, _ in candidates:
            rows.append(
                {
                    "source": job.source,
                    "title": job.title,
                    "company": job.company,
                    "url": _canonical_url(job.source_url),
                    "description": job.description,
                    "created_at": job.created_at,
                    "location": _display_location(job),
                    "raw_data": job.raw_data,
                }
            )
        self.db.upsert_many(rows)

        scored_candidates = [
            (
                job,
                score,
                matched,
                missing,
                eligibility_status,
                eligibility_reason,
                _job_check_score(
                    job, matched, len(unique_skills), eligibility_reason
                ),
            )
            for job, score, matched, missing, eligibility_status, eligibility_reason
            in candidates
        ]
        scored_candidates.sort(
            key=lambda x: (
                -x[6].overall_score,
                -x[1],
                x[0].created_at or "",
                x[0].source,
                x[0].source_url,
            )
        )

        items = tuple(
            HuntItem(
                job_id=_job_id(job),
                source=job.source,
                title=job.title,
                company=job.company,
                url=_canonical_url(job.source_url),
                location=_display_location(job),
                description=job.description,
                fit_score=score,
                overall_score=job_score.overall_score,
                score_breakdown=tuple(
                    {
                        "name": component.name,
                        "points": component.points,
                        "maximum": component.maximum,
                        "status": component.status,
                        "reason": component.reason,
                    }
                    for component in job_score.components
                ),
                score_warnings=job_score.warnings,
                matched_skills=matched,
                missing_skills=missing,
                raw_data={
                    **dict(job.raw_data),
                    "eligibility_status": eligibility_status,
                    "eligibility_reason": eligibility_reason,
                    "fit_basis": "matched requested skills / requested skills",
                },
            )
            for (
                job,
                score,
                matched,
                missing,
                eligibility_status,
                eligibility_reason,
                job_score,
            ) in scored_candidates[:limit]
        )
        return HuntReport(items=items, sources=tuple(health))
