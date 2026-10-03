from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any

from incomeos.jobs.models.job import Job


_TECHNICAL_ROLE = re.compile(
    r"\b(developer|engineer|engineering|programmer|software|backend|frontend|"
    r"full[ -]?stack|devops|sre|site reliability|data scientist|data engineer|"
    r"qa|test engineer|sdet|coder)\b",
    re.I,
)
_SENIORITY = re.compile(
    r"\b(intern|internship|junior|entry[- ]level|mid[- ]level|senior|lead|principal|staff)\b",
    re.I,
)
_EMPLOYMENT_KEYS = ("employment_type", "employmentType", "job_type", "jobType", "type")
_SALARY_KEYS = ("salary", "salary_range", "salaryRange", "compensation", "pay")
_DATE_FORMATS = (
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
)


@dataclass(frozen=True)
class ScoreComponent:
    name: str
    points: int
    maximum: int
    status: str
    reason: str


@dataclass(frozen=True)
class JobScore:
    overall_score: int
    components: tuple[ScoreComponent, ...]
    warnings: tuple[str, ...]


def _raw(job: Job) -> dict[str, Any]:
    return job.raw_data if isinstance(job.raw_data, dict) else {}


def _text(job: Job) -> str:
    return f"{job.title} {job.description}".strip()


def _first_value(raw: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = raw.get(key)
        if value is not None and str(value).strip():
            return value
    return None


def _freshness_points(created_at: str) -> tuple[int, str]:
    value = (created_at or "").strip()
    if not value:
        return 0, "created_at is missing"
    parsed: datetime | None = None
    for fmt in _DATE_FORMATS:
        try:
            parsed = datetime.strptime(value.replace("Z", "+00:00"), fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        return 0, "created_at could not be parsed"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() / 86400)
    if age_days <= 7:
        return 5, f"posted {age_days:.1f} days ago"
    if age_days <= 14:
        return 4, f"posted {age_days:.1f} days ago"
    if age_days <= 30:
        return 3, f"posted {age_days:.1f} days ago"
    if age_days <= 60:
        return 2, f"posted {age_days:.1f} days ago"
    if age_days <= 90:
        return 1, f"posted {age_days:.1f} days ago"
    return 0, f"posted {age_days:.1f} days ago"


def score_job(
    job: Job,
    *,
    matched_skills: tuple[str, ...],
    requested_skill_count: int,
    eligibility_reason: str,
) -> JobScore:
    """Conservative 100-point job-check score.

    Points are awarded only for evidence present in the listing. Missing
    evidence earns zero rather than an invented positive score. This score is
    a screening/check score, not a hiring probability or salary prediction.
    """
    warnings: list[str] = []
    components: list[ScoreComponent] = []

    skill_points = round(40 * len(matched_skills) / requested_skill_count) if requested_skill_count else 0
    components.append(ScoreComponent(
        "skill_match", skill_points, 40,
        "PASS" if skill_points else "FAIL",
        f"{len(matched_skills)}/{requested_skill_count} requested skills explicitly matched",
    ))

    components.append(ScoreComponent(
        "location_eligibility", 20, 20, "PASS",
        eligibility_reason or "target-country eligibility passed",
    ))

    text = _text(job)
    if _TECHNICAL_ROLE.search(job.title) and matched_skills:
        role_points, role_reason = 15, "technical role title with matched skill evidence"
    elif _TECHNICAL_ROLE.search(text) and matched_skills:
        role_points, role_reason = 10, "technical role evidence appears in listing text"
    else:
        role_points, role_reason = 0, "technical role evidence is insufficient"
    components.append(ScoreComponent("role_relevance", role_points, 15, "PASS" if role_points else "UNKNOWN", role_reason))

    seniority = _SENIORITY.search(text)
    if seniority:
        seniority_points = 10
        seniority_reason = f"explicit seniority/level evidence: {seniority.group(1)}"
    else:
        seniority_points = 0
        seniority_reason = "seniority/experience requirement not stated"
        warnings.append("seniority compatibility is unknown")
    components.append(ScoreComponent(
        "seniority_evidence", seniority_points, 10,
        "PASS" if seniority_points else "UNKNOWN", seniority_reason,
    ))

    raw = _raw(job)
    employment = _first_value(raw, _EMPLOYMENT_KEYS)
    if employment is not None:
        components.append(ScoreComponent(
            "employment_type_evidence", 5, 5, "PASS",
            f"employment type is explicitly stated: {employment}",
        ))
    else:
        components.append(ScoreComponent(
            "employment_type_evidence", 0, 5, "UNKNOWN",
            "employment type is not stated",
        ))
        warnings.append("employment type is unknown")

    salary = _first_value(raw, _SALARY_KEYS)
    if salary is not None:
        components.append(ScoreComponent(
            "compensation_evidence", 5, 5, "PASS",
            "compensation information is explicitly stated",
        ))
    else:
        components.append(ScoreComponent(
            "compensation_evidence", 0, 5, "UNKNOWN",
            "compensation is not stated",
        ))
        warnings.append("salary/compensation is unknown")

    freshness_points, freshness_reason = _freshness_points(job.created_at)
    components.append(ScoreComponent(
        "freshness", freshness_points, 5,
        "PASS" if freshness_points >= 3 else "UNKNOWN",
        freshness_reason,
    ))
    if freshness_points == 0:
        warnings.append("job freshness is unknown or the listing is older than 90 days")

    return JobScore(
        overall_score=sum(component.points for component in components),
        components=tuple(components),
        warnings=tuple(warnings),
    )
