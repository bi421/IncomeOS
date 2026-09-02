from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class EvidenceType(StrEnum):
    REPOSITORY = "repository"
    CODE = "code"
    TEST = "test"
    DOCUMENTATION = "documentation"
    BENCHMARK = "benchmark"
    DEPLOYMENT = "deployment"


class EvidenceDimension(StrEnum):
    PRESENCE = "presence"
    USAGE = "usage"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    ENGINEERING = "engineering"


@dataclass(frozen=True)
class SkillEvidence:
    skill: str
    evidence_type: EvidenceType
    source: str
    description: str
    strength: float
    dimension: EvidenceDimension = EvidenceDimension.PRESENCE

    def __post_init__(self) -> None:
        if not self.skill.strip():
            raise ValueError("skill must not be empty")

        if not self.source.strip():
            raise ValueError("source must not be empty")

        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("strength must be between 0 and 1")


@dataclass(frozen=True)
class Skill:
    name: str
    category: str
    evidence: tuple[SkillEvidence, ...] = field(
        default_factory=tuple
    )

    @property
    def evidence_strength(self) -> float:
        if not self.evidence:
            return 0.0

        return max(
            item.strength
            for item in self.evidence
        )