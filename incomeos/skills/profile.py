from __future__ import annotations

from .evidence import build_skills
from .models import EvidenceType, Skill, SkillEvidence


def build_bold_profile() -> tuple[Skill, ...]:
    evidence = [
        SkillEvidence(
            skill="Python",
            evidence_type=EvidenceType.REPOSITORY,
            source="bi421/ResearchOS",
            description=(
                "Built a deterministic market research platform "
                "with a substantial Python package and test suite."
            ),
            strength=0.95,
        ),
        SkillEvidence(
            skill="Data Engineering",
            evidence_type=EvidenceType.REPOSITORY,
            source="bi421/ResearchOS",
            description=(
                "Implemented market data loading, validation, "
                "provenance and processing workflows."
            ),
            strength=0.90,
        ),
        SkillEvidence(
            skill="C++",
            evidence_type=EvidenceType.REPOSITORY,
            source="bi421/ResearchOS",
            description=(
                "Implemented and integrated a C++ quantitative "
                "backend for performance-sensitive computation."
            ),
            strength=0.85,
        ),
        SkillEvidence(
            skill="Testing",
            evidence_type=EvidenceType.TEST,
            source="bi421/ResearchOS",
            description=(
                "Maintained a large automated test suite and "
                "used deterministic validation."
            ),
            strength=0.95,
        ),
        SkillEvidence(
            skill="Flask",
            evidence_type=EvidenceType.REPOSITORY,
            source="bi421/fb-planner-audit",
            description=(
                "Built a Flask-based Messenger application "
                "with webhook and scheduled processing."
            ),
            strength=0.85,
        ),
        SkillEvidence(
            skill="SQLite",
            evidence_type=EvidenceType.CODE,
            source="bi421/fb-planner-audit",
            description="Implemented a SQLite storage layer.",
            strength=0.80,
        ),
        SkillEvidence(
            skill="Pydantic",
            evidence_type=EvidenceType.CODE,
            source="bi421/fb-planner-audit",
            description="Used Pydantic models for application data.",
            strength=0.80,
        ),
        SkillEvidence(
            skill="Automation",
            evidence_type=EvidenceType.DEPLOYMENT,
            source="bi421/fb-planner-audit",
            description=(
                "Implemented scheduled policy updates and "
                "background auditing."
            ),
            strength=0.85,
        ),
    ]

    return build_skills(evidence)