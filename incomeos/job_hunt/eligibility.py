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
_WORLDWIDE = re.compile(
    r"\b(worldwide|anywhere in the world|work from anywhere|global)\b",
    re.I,
)


def _as_text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _contains_target(value: object, target: str) -> bool:
    return target in _as_text(value).lower()


def _allowed_location_status(
    value: object,
    target: str,
) -> str | None:
    text = _as_text(value)
    if not text:
        return None
    lowered = text.lower()
    if _WORLDWIDE.search(lowered) or target in lowered:
        return "PASS"
    return "FAIL"


def _text(job: Job) -> tuple[str, str]:
    raw = job.raw_data if isinstance(job.raw_data, dict) else {}
    location_values: list[str] = []
    for key in (
        "location",
        "candidate_required_location",
        "candidate_location",
        "job_location",
        "country",
        "region",
        "state",
    ):
        value = _as_text(raw.get(key))
        if value:
            location_values.append(value)
    restrictions = raw.get("locationRestrictions")
    if isinstance(restrictions, (list, tuple, set)):
        location_values.extend(
            _as_text(value) for value in restrictions if _as_text(value)
        )
    location = " | ".join(dict.fromkeys(location_values))
    combined = " ".join(
        part for part in (job.title, job.description, location) if part
    )
    return combined, location


def assess_eligibility(job: Job, target_country: str = "Mongolia") -> EligibilityResult:
    """Conservative eligibility gate: explicit restrictions override generic remote text."""
    combined, location = _text(job)
    target = target_country.strip().lower()
    if not target:
        raise ValueError("target_country must not be empty")

    for pattern in _RESTRICTED:
        if pattern.search(combined):
            return EligibilityResult(
                "FAIL", "explicit geographic or citizenship restriction", None, location
            )

    raw = job.raw_data if isinstance(job.raw_data, dict) else {}

    for key in ("locationRestrictions", "candidate_required_location"):
        value = raw.get(key)
        if isinstance(value, (list, tuple, set)):
            values = tuple(_as_text(item) for item in value if _as_text(item))
            if values:
                if any(_WORLDWIDE.search(item.lower()) or target in item.lower() for item in values):
                    return EligibilityResult(
                        "PASS", f"{key} explicitly permits the target country", True, location
                    )
                return EligibilityResult(
                    "FAIL", f"{key} excludes the target country", None, location
                )
        elif _as_text(value):
            status = _allowed_location_status(value, target)
            if status == "PASS":
                return EligibilityResult(
                    "PASS", f"{key} explicitly permits the target country", True, location
                )
            if status == "FAIL":
                return EligibilityResult(
                    "FAIL", f"{key} excludes the target country", None, location
                )

    countries = raw.get("countries")
    if isinstance(countries, (list, tuple, set)):
        normalized = {_as_text(x).lower() for x in countries if _as_text(x)}
        if normalized and target not in normalized and not any(
            _WORLDWIDE.search(x) for x in normalized
        ):
            return EligibilityResult(
                "FAIL", "target country not listed in allowed countries", None, location
            )

    region = _as_text(raw.get("region"))
    country = _as_text(raw.get("country"))
    for value, label in ((region, "region"), (country, "country")):
        if value:
            status = _allowed_location_status(value, target)
            if status == "FAIL":
                return EligibilityResult(
                    "FAIL", f"{label} excludes the target country", None, location
                )
            if status == "PASS":
                return EligibilityResult(
                    "PASS", f"{label} explicitly permits the target country", True, location
                )

    target_excluded = bool(re.search(rf"\b(?:except|excluding|not available in|unavailable in|no hiring in)\s+(?:[a-z ,/&-]*\b)?{re.escape(target)}\b", combined, re.I))
    if target_excluded:
        return EligibilityResult("FAIL", "target country is explicitly excluded", None, location)

    remote = bool(_EXPLICIT_REMOTE.search(combined))
    match = _COUNTRY_RE.search(combined)
    if match and target not in match.group(1).lower() and not remote:
        return EligibilityResult(
            "UNKNOWN", "location restriction could not be verified", remote, location
        )

    if remote:
        return EligibilityResult(
            "UNKNOWN",
            "remote work is stated, but target-country eligibility is not explicit",
            True,
            location,
        )

    if _contains_target(location, target):
        return EligibilityResult(
            "PASS", "target country appears in the job location", False, location
        )

    return EligibilityResult(
        "UNKNOWN", "no reliable location eligibility evidence", None, location
    )
