from __future__ import annotations

from dataclasses import dataclass
import re

from incomeos.jobs.models.job import Job


@dataclass(frozen=True)
class EligibilityResult:
    status: str
    reason: str
    remote: bool | None
    location_text: str


_EXPLICIT_REMOTE = re.compile(
    r"\b(remote|work from anywhere|distributed|100% remote|anywhere in the world)\b",
    re.I,
)
_RESTRICTED = (
    re.compile(
        r"\b(us only|usa only|united states only|remote\s*[-–]\s*(?:us|usa)|"
        r"must be (?:located|based) in the (?:us|usa|united states))\b",
        re.I,
    ),
    re.compile(
        r"\b(uk only|united kingdom only|must be (?:located|based) in the uk)\b",
        re.I,
    ),
    re.compile(
        r"\b(eu only|european union only|must be (?:located|based) in the eu)\b",
        re.I,
    ),
    re.compile(
        r"\b(?:requires?|must have|need(?:s)?)\s+(?:to be\s+)?"
        r"(?:a\s+)?(?:us|u\.s\.?|usa|united states)\s+citizenship\b",
        re.I,
    ),
)
_COUNTRY_RE = re.compile(
    r"\b(?:location|locations?|based in|located in|eligible in|hiring in)"
    r"\s*[:\-]?\s*([^\n.;]{2,120})",
    re.I,
)


def _text(job: Job) -> tuple[str, str]:
    raw = job.raw_data if isinstance(job.raw_data, dict) else {}
    location = str(
        raw.get("location")
        or raw.get("candidate_required_location")
        or raw.get("candidate_location")
        or raw.get("job_location")
        or ""
    ).strip()
    combined = " ".join(
        part for part in (job.title, job.description, location) if part
    )
    return combined, location


def assess_eligibility(job: Job, target_country: str = "Mongolia") -> EligibilityResult:
    """Conservative eligibility gate: unknown never becomes PASS."""
    combined, location = _text(job)
    target = target_country.strip().lower()
    if not target:
        raise ValueError("target_country must not be empty")

    for pattern in _RESTRICTED:
        if pattern.search(combined):
            return EligibilityResult(
                "FAIL", "explicit geographic or citizenship restriction", None, location
            )

    remote = bool(_EXPLICIT_REMOTE.search(combined))
    raw = job.raw_data if isinstance(job.raw_data, dict) else {}

    countries = raw.get("countries")
    if isinstance(countries, (list, tuple, set)):
        normalized = {str(x).strip().lower() for x in countries if str(x).strip()}
        if normalized and target not in normalized and "worldwide" not in normalized:
            return EligibilityResult(
                "FAIL", "target country not listed in allowed countries", remote, location
            )

    match = _COUNTRY_RE.search(combined)
    if match and target not in match.group(1).lower() and remote is False:
        return EligibilityResult(
            "UNKNOWN", "location restriction could not be verified", remote, location
        )

    if remote:
        return EligibilityResult(
            "PASS",
            "remote work is explicitly indicated and no conflicting restriction was found",
            True,
            location,
        )

    if target in location.lower():
        return EligibilityResult(
            "PASS", "target country appears in the job location", False, location
        )

    return EligibilityResult(
        "UNKNOWN", "no reliable location eligibility evidence", None, location
    )
