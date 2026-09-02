from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from incomeos.skills.aggregator import build_master_profile
from incomeos.skills.levels import (
    CapabilityLevel,
    classify_capability_level,
)
from incomeos.skills.github_analyzer import analyze_repository
from incomeos.skills.detector import detect_skills


@dataclass(frozen=True)
class Capability:
    """
    A capability is a higher-level professional ability supported by
    one or more verified skills.

    ``confidence`` measures evidence confidence.

    ``level`` measures evidence-backed capability breadth.

    These are intentionally separate concepts.
    """

    name: str
    category: str
    skills: tuple[str, ...]
    evidence_count: int
    repository_count: int
    confidence: float
    level: CapabilityLevel = CapabilityLevel.UNKNOWN
    level_reason: str = ""


CAPABILITY_RULES: dict[str, tuple[str, ...]] = {
    "Python Application Development": (
        "Python",
    ),
    "Python Automation": (
        "Python",
    ),
    "Automated Testing": (
        "Testing",
    ),
    "Data Processing & Pipeline Development": (
        "Data Engineering",
    ),
    "C++ Systems Development": (
        "C++",
    ),
    "Containerized Application Deployment": (
        "Docker",
    ),
    "C++ Build System Engineering": (
        "CMake",
    ),
}


CAPABILITY_CATEGORIES: dict[str, str] = {
    "Python Application Development": "software",
    "Python Automation": "automation",
    "Automated Testing": "quality",
    "Data Processing & Pipeline Development": "data",
    "C++ Systems Development": "systems",
    "Containerized Application Deployment": "deployment",
    "C++ Build System Engineering": "engineering",
}


def build_capabilities(root: str | Path) -> tuple[Capability, ...]:
    root_path = Path(root)
    profile = build_master_profile(root_path)

    master_skills = {
        skill.name: skill
        for skill in profile.skills
    }

    capabilities: list[Capability] = []

    for capability_name, required_skills in CAPABILITY_RULES.items():
        available = [
            master_skills[skill_name]
            for skill_name in required_skills
            if skill_name in master_skills
        ]

        if not available:
            continue

        evidence_count = sum(
            skill.evidence_count
            for skill in available
        )

        repositories: set[str] = set()

        for skill in available:
            repositories.update(skill.repositories)

        confidence = min(
            1.0,
            sum(skill.confidence for skill in available)
            / len(available),
        )

        confidence = round(confidence, 4)
        repository_count = len(repositories)

        level, reason = classify_capability_level(
            confidence=confidence,
            evidence_count=evidence_count,
            repository_count=repository_count,
        )

        capabilities.append(
            Capability(
                name=capability_name,
                category=CAPABILITY_CATEGORIES[capability_name],
                skills=tuple(required_skills),
                evidence_count=evidence_count,
                repository_count=repository_count,
                confidence=confidence,
                level=level,
                level_reason=reason,
            )
        )

    capabilities.sort(
        key=lambda capability: (
            -capability.confidence,
            -capability.evidence_count,
            capability.name.lower(),
        )
    )

    return tuple(capabilities)


def main() -> None:
    root = Path("data/github_repos")

    capabilities = build_capabilities(root)

    print()
    print("INCOMEOS CAPABILITY PROFILE")
    print("===========================")
    print(f"CAPABILITIES: {len(capabilities)}")
    print()

    for capability in capabilities:
        print(
            f"{capability.name}: "
            f"{capability.level.value} "
            f"confidence={capability.confidence:.2f} "
            f"(category={capability.category}; "
            f"evidence={capability.evidence_count}; "
            f"repos={capability.repository_count}; "
            f"skills={', '.join(capability.skills)}; "
            f"reason={capability.level_reason})"
        )


if __name__ == "__main__":
    main()
