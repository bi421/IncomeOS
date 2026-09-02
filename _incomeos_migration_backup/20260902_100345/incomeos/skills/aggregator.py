from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import EvidenceDimension
from .portfolio import build_portfolio


DIMENSION_WEIGHTS: dict[EvidenceDimension, float] = {
    EvidenceDimension.PRESENCE: 0.40,
    EvidenceDimension.USAGE: 0.70,
    EvidenceDimension.ENGINEERING: 0.75,
    EvidenceDimension.VALIDATION: 0.90,
    EvidenceDimension.IMPLEMENTATION: 1.00,
}


@dataclass(frozen=True)
class MasterSkill:
    name: str
    confidence: float
    evidence_count: int
    repositories: tuple[str, ...]


@dataclass(frozen=True)
class MasterSkillProfile:
    repository_count: int
    skill_record_count: int
    skills: tuple[MasterSkill, ...]


def build_master_profile(
    root: str | Path,
) -> MasterSkillProfile:
    portfolio = build_portfolio(root)

    aggregated: dict[str, dict] = {}

    for report in portfolio.repositories:
        for skill in report.skills:
            name = skill.name

            if name not in aggregated:
                aggregated[name] = {
                    "repository_scores": {},
                    "evidence_count": 0,
                    "repositories": set(),
                }

            repository = report.repository

            if repository not in aggregated[name]["repository_scores"]:
                aggregated[name]["repository_scores"][repository] = 0.0

            for evidence in skill.evidence:
                dimension_weight = DIMENSION_WEIGHTS[
                    evidence.dimension
                ]

                weighted_strength = (
                    float(evidence.strength)
                    * dimension_weight
                )

                aggregated[name]["repository_scores"][repository] = max(
                    aggregated[name]["repository_scores"][repository],
                    weighted_strength,
                )

                aggregated[name]["evidence_count"] += 1

            aggregated[name]["repositories"].add(repository)

    master_skills: list[MasterSkill] = []

    for name, data in aggregated.items():
        repository_scores = data["repository_scores"]

        if not repository_scores:
            confidence = 0.0
        else:
            strongest_score = max(
                repository_scores.values()
            )

            repository_count = len(repository_scores)

            repetition_bonus = min(
                0.20,
                0.05 * max(repository_count - 1, 0),
            )

            confidence = min(
                1.0,
                strongest_score + repetition_bonus,
            )

        master_skills.append(
            MasterSkill(
                name=name,
                confidence=round(confidence, 4),
                evidence_count=data["evidence_count"],
                repositories=tuple(
                    sorted(data["repositories"])
                ),
            )
        )

    master_skills.sort(
        key=lambda skill: (
            -skill.confidence,
            -skill.evidence_count,
            skill.name.lower(),
        )
    )

    return MasterSkillProfile(
        repository_count=portfolio.repository_count,
        skill_record_count=portfolio.total_skill_count,
        skills=tuple(master_skills),
    )


def save_master_profile(
    profile: MasterSkillProfile,
    output: str | Path,
) -> Path:
    output_path = Path(output)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "repository_count": profile.repository_count,
        "skill_record_count": profile.skill_record_count,
        "unique_skill_count": len(profile.skills),
        "skills": [
            asdict(skill)
            for skill in profile.skills
        ],
    }

    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return output_path
