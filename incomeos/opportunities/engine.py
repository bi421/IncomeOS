from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from incomeos.skills.levels import (
    CapabilityLevel,
    capability_readiness_score,
)


@dataclass(frozen=True)
class IncomeOpportunity:
    name: str
    description: str
    required_skills: tuple[str, ...]
    skill_weights: tuple[float, ...]
    base_value: float
    difficulty: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name must not be empty")

        if not self.required_skills:
            raise ValueError("required_skills must not be empty")

        if len(self.required_skills) != len(self.skill_weights):
            raise ValueError(
                "required_skills and skill_weights must have equal length"
            )

        if any(w < 0.0 for w in self.skill_weights):
            raise ValueError(
                "skill weights must not be negative"
            )

        if sum(self.skill_weights) <= 0.0:
            raise ValueError(
                "skill weights must have positive total"
            )

        if not 0.0 <= self.base_value <= 1.0:
            raise ValueError(
                "base_value must be between 0 and 1"
            )

        if not 0.0 <= self.difficulty <= 1.0:
            raise ValueError(
                "difficulty must be between 0 and 1"
            )


@dataclass(frozen=True)
class OpportunityMatch:
    opportunity: IncomeOpportunity
    readiness: float
    opportunity_score: float
    matched_skills: tuple[str, ...]
    missing_skills: tuple[str, ...]
    readiness_basis: str = "skill_confidence"


DEFAULT_OPPORTUNITIES = (
    IncomeOpportunity(
        name="Python Automation",
        description="Python scripting and automation work.",
        required_skills=("Python", "Testing"),
        skill_weights=(0.5, 0.5),
        base_value=0.9,
        difficulty=0.35,
    ),
    IncomeOpportunity(
        name="Data Engineering Support",
        description="Data pipelines, databases, and data processing support.",
        required_skills=("Python", "Data Engineering"),
        skill_weights=(0.4, 0.6),
        base_value=0.85,
        difficulty=0.45,
    ),
    IncomeOpportunity(
        name="C++ Quant / Performance Engineering",
        description="C++ performance and quantitative engineering work.",
        required_skills=("C++", "Python", "Testing"),
        skill_weights=(0.4, 0.25, 0.35),
        base_value=0.95,
        difficulty=0.7,
    ),
    IncomeOpportunity(
        name="Docker Deployment Support",
        description="Containerization and deployment support.",
        required_skills=("Docker", "Python"),
        skill_weights=(0.6, 0.4),
        base_value=0.75,
        difficulty=0.5,
    ),
    IncomeOpportunity(
        name="Build System Engineering",
        description="CMake and software build-system support.",
        required_skills=("CMake", "C++"),
        skill_weights=(0.45, 0.55),
        base_value=0.7,
        difficulty=0.6,
    ),
)


def _extract_skills(profile: Any) -> Iterable[Any]:
    if isinstance(profile, dict):
        return profile.get("skills", ())

    skills = getattr(profile, "skills", None)

    if skills is not None:
        return skills

    raise TypeError(
        "profile must be a mapping with 'skills' or "
        "an object with a 'skills' attribute"
    )


def _extract_capabilities(profile: Any) -> tuple[Any, ...]:
    if isinstance(profile, dict):
        value = profile.get("capabilities")
        if value is None:
            return ()
        return tuple(value)

    value = getattr(profile, "capabilities", None)

    if value is None:
        return ()

    return tuple(value)


def _skill_name(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("name", ""))

    return str(getattr(item, "name", ""))


def _skill_confidence(item: Any) -> float:
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


def _capability_skills(item: Any) -> tuple[str, ...]:
    if isinstance(item, dict):
        skills = item.get("skills", ())
    else:
        skills = getattr(item, "skills", ())

    return tuple(str(skill) for skill in skills)


def _capability_level(item: Any) -> CapabilityLevel:
    raw = (
        item.get("level", CapabilityLevel.UNKNOWN)
        if isinstance(item, dict)
        else getattr(item, "level", CapabilityLevel.UNKNOWN)
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


def _capability_score_for_skill(
    skill: str,
    capabilities: tuple[Any, ...],
) -> float:
    candidates = []

    for capability in capabilities:
        if skill not in _capability_skills(capability):
            continue

        level = _capability_level(capability)
        confidence = _capability_confidence(capability)

        candidates.append(
            capability_readiness_score(
                level,
                confidence,
            )
        )

    return max(candidates, default=0.0)


def _normalise_profile(
    profile: Any,
) -> dict[str, float]:
    capabilities = _extract_capabilities(profile)

    if capabilities:
        return {
            skill: _capability_score_for_skill(
                skill,
                capabilities,
            )
            for capability in capabilities
            for skill in _capability_skills(capability)
        }

    result: dict[str, float] = {}

    for item in _extract_skills(profile):
        name = _skill_name(item).strip()

        if not name:
            continue

        confidence = _skill_confidence(item)

        current = result.get(name, 0.0)

        result[name] = max(
            current,
            confidence,
        )

    return result


def _profile_readiness_basis(profile: Any) -> str:
    if _extract_capabilities(profile):
        return "capability_level_and_evidence_confidence"

    return "skill_confidence"


def filter_opportunities_by_skills(
    profile: Any,
    opportunities: Iterable[IncomeOpportunity],
    min_confidence: float = 0.5,
) -> tuple[IncomeOpportunity, ...]:
    """
    Filter opportunities by evidence-backed readiness.

    When capability records are supplied, capability level is respected.
    Skill-only profiles retain compatibility with the previous API.
    """

    skill_confidence = _normalise_profile(profile)

    result: list[IncomeOpportunity] = []

    for opportunity in opportunities:
        can_do = True

        for skill in opportunity.required_skills:
            if skill_confidence.get(skill, 0.0) < min_confidence:
                can_do = False
                break

        if can_do:
            result.append(opportunity)

    return tuple(result)


def match_opportunities(
    profile: Any,
    opportunities: Iterable[IncomeOpportunity] = DEFAULT_OPPORTUNITIES,
    min_skill_confidence: float | None = None,
) -> tuple[OpportunityMatch, ...]:
    filtered = (
        filter_opportunities_by_skills(
            profile,
            opportunities,
            min_skill_confidence,
        )
        if min_skill_confidence is not None
        else tuple(opportunities)
    )

    skill_confidence = _normalise_profile(profile)
    readiness_basis = _profile_readiness_basis(profile)

    results: list[OpportunityMatch] = []

    for opportunity in filtered:
        total_weight = sum(opportunity.skill_weights)

        weighted_readiness = 0.0
        matched: list[str] = []
        missing: list[str] = []

        for skill, weight in zip(
            opportunity.required_skills,
            opportunity.skill_weights,
        ):
            confidence = skill_confidence.get(skill, 0.0)

            weighted_readiness += confidence * weight

            if confidence > 0.0:
                matched.append(skill)
            else:
                missing.append(skill)

        readiness = (
            weighted_readiness / total_weight
            if total_weight > 0.0
            else 0.0
        )

        opportunity_score = (
            readiness
            * opportunity.base_value
            * (1.0 - 0.5 * opportunity.difficulty)
        )

        results.append(
            OpportunityMatch(
                opportunity=opportunity,
                readiness=round(readiness, 6),
                opportunity_score=round(
                    opportunity_score,
                    6,
                ),
                matched_skills=tuple(matched),
                missing_skills=tuple(missing),
                readiness_basis=readiness_basis,
            )
        )

    results.sort(
        key=lambda item: (
            item.opportunity_score,
            item.readiness,
            item.opportunity.base_value,
        ),
        reverse=True,
    )

    return tuple(results)


if __name__ == "__main__":
    from incomeos.skills.aggregator import build_master_profile
    from incomeos.skills.capabilities import build_capabilities

    root = "data/github_repos"

    master_profile = build_master_profile(root)
    capabilities = build_capabilities(root)

    profile = {
        "skills": master_profile.skills,
        "capabilities": capabilities,
    }

    matches = match_opportunities(
        profile,
        min_skill_confidence=0.5,
    )

    print()
    print("INCOMEOS OPPORTUNITY PROFILE")
    print("============================")

    for i, item in enumerate(
        matches,
        start=1,
    ):
        print(
            f"{i}. {item.opportunity.name} | "
            f"readiness={item.readiness:.3f} | "
            f"score={item.opportunity_score:.3f} | "
            f"basis={item.readiness_basis} | "
            f"matched={item.matched_skills} | "
            f"missing={item.missing_skills}"
        )
