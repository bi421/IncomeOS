from __future__ import annotations

from dataclasses import dataclass, field

from incomeos.skills.aggregator import MasterSkill, MasterSkillProfile
from incomeos.skills.levels import CapabilityLevel, classify_capability_level


@dataclass(frozen=True)
class CapabilityEvidence:
    """
    A single addressable evidence record backing a Capability.

    M1 derives these from the facts MasterSkill already carries
    (repositories, verified_decision_ids) so nothing upstream changes.
    M2's GitHub-evidence -> domain-capability extraction will populate
    these directly instead of deriving them.
    """

    repository: str
    verified: bool = False
    decision_id: str = ""


@dataclass(frozen=True)
class Capability:
    """
    M1 abstraction layer: MasterSkill -> Capability.

    Intentionally 1:1 with the underlying skill for now (name == skill.name,
    skills == (skill.name,)), so incomeos.jobs.fit.evaluate_job_fit keeps
    working unmodified against a CapabilityProfile. M2 will introduce
    many-skills-per-capability grouping here.
    """

    name: str
    skills: tuple[str, ...]
    confidence: float
    level: str
    evidence: tuple[CapabilityEvidence, ...] = field(default_factory=tuple)
    evidence_count: int = 0
    repositories: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "skills": self.skills,
            "confidence": self.confidence,
            "level": self.level,
        }


@dataclass(frozen=True)
class CapabilityProfile:
    """
    Drop-in replacement for MasterSkillProfile as a `profile` argument to
    evaluate_job_fit: exposes `.capabilities` so
    incomeos.jobs.fit._extract_capabilities picks it up via its
    getattr(profile, "capabilities", ()) fallback branch.
    """

    repository_count: int
    capabilities: tuple[Capability, ...]


def capability_from_master_skill(skill: MasterSkill) -> Capability:
    level, _ = classify_capability_level(
        confidence=skill.confidence,
        evidence_count=skill.evidence_count,
        repository_count=len(skill.repositories),
    )

    repo_evidence = tuple(
        CapabilityEvidence(repository=repository, verified=False)
        for repository in skill.repositories
    )

    verified_evidence = tuple(
        CapabilityEvidence(repository="verified", verified=True, decision_id=decision_id)
        for decision_id in skill.verified_decision_ids
    )

    return Capability(
        name=skill.name,
        skills=(skill.name,),
        confidence=skill.confidence,
        level=level.value,
        evidence=repo_evidence + verified_evidence,
        evidence_count=skill.evidence_count,
        repositories=skill.repositories,
    )


def build_capability_profile(profile: MasterSkillProfile) -> CapabilityProfile:
    return CapabilityProfile(
        repository_count=profile.repository_count,
        capabilities=tuple(
            capability_from_master_skill(skill) for skill in profile.skills
        ),
    )

