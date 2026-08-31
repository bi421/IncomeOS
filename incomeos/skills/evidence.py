from __future__ import annotations

from collections import defaultdict

from .models import Skill, SkillEvidence


def build_skill_index(
    evidence: list[SkillEvidence],
) -> dict[str, list[SkillEvidence]]:
    index: dict[str, list[SkillEvidence]] = defaultdict(list)

    for item in evidence:
        index[item.skill].append(item)

    return dict(index)


def build_skills(
    evidence: list[SkillEvidence],
) -> tuple[Skill, ...]:
    index = build_skill_index(evidence)

    skills: list[Skill] = []

    for skill_name, items in sorted(index.items()):
        skills.append(
            Skill(
                name=skill_name,
                category=_infer_category(skill_name),
                evidence=tuple(items),
            )
        )

    return tuple(skills)


def _infer_category(skill: str) -> str:
    normalized = skill.lower()

    if normalized in {
        "python",
        "c++",
        "flask",
        "pydantic",
    }:
        return "software"

    if normalized in {
        "polars",
        "pandas",
        "numpy",
        "data engineering",
        "statistics",
    }:
        return "data"

    if normalized in {
        "git",
        "github",
        "pytest",
        "ruff",
        "cmake",
    }:
        return "engineering"

    if normalized in {
        "quantitative research",
        "market research",
        "quantitative analysis",
    }:
        return "research"

    return "other"