from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from incomeos.skills.levels import CapabilityLevel, classify_capability_level


_LEVEL_RANK = {
    CapabilityLevel.UNKNOWN: 0,
    CapabilityLevel.B: 1,
    CapabilityLevel.A: 2,
}


@dataclass(frozen=True)
class JobRequirement:
    skill: str
    minimum_level: CapabilityLevel = CapabilityLevel.B

    def __post_init__(self) -> None:
        if not self.skill.strip():
            raise ValueError("skill must not be empty")


@dataclass(frozen=True)
class JobFit:
    job_id: str
    fit_score: float
    matched_requirements: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    reasons: tuple[str, ...]

    @property
    def is_qualified(self) -> bool:
        return bool(
            self.matched_requirements
        ) and not self.missing_requirements


def _capability_name(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("name", "")).strip()
    return str(getattr(item, "name", "")).strip()


def _capability_skills(item: Any) -> tuple[str, ...]:
    if isinstance(item, dict):
        value = item.get("skills", ())
    else:
        value = getattr(item, "skills", ())

    return tuple(str(x) for x in value)


def _capability_level(item: Any) -> CapabilityLevel:
    if isinstance(item, dict):
        raw = item.get(
            "level",
            CapabilityLevel.UNKNOWN.value,
        )
    else:
        raw = getattr(
            item,
            "level",
            CapabilityLevel.UNKNOWN,
        )

    try:
        return CapabilityLevel(raw)
    except (ValueError, TypeError):
        return CapabilityLevel.UNKNOWN


def _capability_confidence(item: Any) -> float:
    if isinstance(item, dict):
        value = item.get("confidence", 0.0)
    else:
        value = getattr(item, "confidence", 0.0)

    try:
        return max(
            0.0,
            min(1.0, float(value)),
        )
    except (TypeError, ValueError):
        return 0.0


def _extract_capabilities(profile: Any) -> tuple[Any, ...]:
    if isinstance(profile, dict):
        value = profile.get("capabilities", ())
        if value:
            return tuple(value)

        skills = profile.get("skills", ())
        if not skills:
            return ()

        capabilities = []
        for skill in skills:
            level, _ = classify_capability_level(
                confidence=skill.confidence,
                evidence_count=skill.evidence_count,
                repository_count=len(skill.repositories),
            )
            capabilities.append(
                {
                    "name": skill.name,
                    "skills": (skill.name,),
                    "confidence": skill.confidence,
                    "level": level.value,
                }
            )
        return tuple(capabilities)

    skills = getattr(profile, "skills", None)
    if skills is not None:
        capabilities = []
        for skill in skills:
            level, _ = classify_capability_level(
                confidence=skill.confidence,
                evidence_count=skill.evidence_count,
                repository_count=len(skill.repositories),
            )
            capabilities.append(
                {
                    "name": skill.name,
                    "skills": (skill.name,),
                    "confidence": skill.confidence,
                    "level": level.value,
                }
            )
        return tuple(capabilities)

    value = getattr(profile, "capabilities", ())
    return tuple(value or ())

def evaluate_job_fit(
    *,
    job_id: str,
    requirements: Iterable[JobRequirement],
    profile: Any,
) -> JobFit:
    requirements = tuple(requirements)

    if not job_id.strip():
        raise ValueError("job_id must not be empty")

    capabilities = _extract_capabilities(profile)

    matched: list[str] = []
    missing: list[str] = []
    reasons: list[str] = []

    if not requirements:
        return JobFit(
            job_id=job_id,
            fit_score=0.0,
            matched_requirements=(),
            missing_requirements=(),
            reasons=("job has no declared requirements",),
        )

    for requirement in requirements:
        candidates = [
            capability
            for capability in capabilities
            if requirement.skill
            in _capability_skills(capability)
        ]

        if not candidates:
            missing.append(requirement.skill)
            reasons.append(
                f"{requirement.skill}: no capability evidence"
            )
            continue

        best = max(
            candidates,
            key=lambda item: (
                _LEVEL_RANK[_capability_level(item)],
                _capability_confidence(item),
            ),
        )

        level = _capability_level(best)
        confidence = _capability_confidence(best)

        if (
            _LEVEL_RANK[level]
            >= _LEVEL_RANK[requirement.minimum_level]
        ):
            matched.append(requirement.skill)
            reasons.append(
                f"{requirement.skill}: "
                f"level={level.value}; "
                f"confidence={confidence:.2f}"
            )
        else:
            missing.append(requirement.skill)
            reasons.append(
                f"{requirement.skill}: "
                f"level={level.value} below required "
                f"{requirement.minimum_level.value}; "
                f"confidence={confidence:.2f}"
            )

    fit_score = (
        len(matched) / len(requirements)
        if requirements
        else 0.0
    )

    return JobFit(
        job_id=job_id,
        fit_score=round(fit_score, 6),
        matched_requirements=tuple(matched),
        missing_requirements=tuple(missing),
        reasons=tuple(reasons),
    )



