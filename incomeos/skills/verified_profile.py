
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from incomeos.skills.verification import (
    VerificationRecord,
    VerificationStatus,
)


@dataclass(frozen=True)
class VerifiedSkillProjection:
    skill: str
    verified_evidence_count: int
    verified_decision_ids: tuple[str, ...]
    verified_job_ids: tuple[str, ...]
    verified_sources: tuple[str, ...]


@dataclass(frozen=True)
class VerifiedProfileProjection:
    skills: tuple[VerifiedSkillProjection, ...]


def build_verified_profile_projection(
    records: tuple[VerificationRecord, ...],
) -> VerifiedProfileProjection:
    grouped: dict[str, list[VerificationRecord]] = {}

    for record in records:
        if record.status is not VerificationStatus.VERIFIED:
            continue

        grouped.setdefault(
            record.skill,
            [],
        ).append(record)

    skills: list[VerifiedSkillProjection] = []

    for skill, items in sorted(grouped.items()):
        skills.append(
            VerifiedSkillProjection(
                skill=skill,
                verified_evidence_count=len(items),
                verified_decision_ids=tuple(
                    sorted(
                        {item.decision_id for item in items}
                    )
                ),
                verified_job_ids=tuple(
                    sorted(
                        {item.job_id for item in items}
                    )
                ),
                verified_sources=tuple(
                    sorted(
                        {item.evidence_source for item in items}
                    )
                ),
            )
        )

    return VerifiedProfileProjection(
        skills=tuple(skills)
    )


def save_verified_profile_projection(
    profile: VerifiedProfileProjection,
    output: str | Path,
) -> Path:
    path = Path(output)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "verified_skill_count": len(profile.skills),
        "skills": [
            {
                "skill": item.skill,
                "verified_evidence_count": item.verified_evidence_count,
                "verified_decision_ids": list(
                    item.verified_decision_ids
                ),
                "verified_job_ids": list(
                    item.verified_job_ids
                ),
                "verified_sources": list(
                    item.verified_sources
                ),
            }
            for item in profile.skills
        ],
    }

    path.write_text(
        __import__("json").dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return path
