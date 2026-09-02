from __future__ import annotations

from incomeos.capabilities.models import (
    Capability,
    CapabilityEvidence,
    CapabilityProfile,
    build_capability_profile,
)
from incomeos.skills.aggregator import MasterSkill, MasterSkillProfile
from incomeos.skills.levels import classify_capability_level


# M2 draft taxonomy â€” skill names below must match incomeos.jobs.requirements.SKILL_ALIASES keys.
# This grouping is a first pass based on the skill vocabulary already in the codebase.
# Edit freely: add/remove domains, move skills between domains, or add new skill names
# as SKILL_ALIASES grows. A domain is only ever built if at least one of its member
# skills actually has evidence in the profile â€” an empty/unmatched domain never appears.
DOMAIN_TAXONOMY: dict[str, tuple[str, ...]] = {
    "Backend Engineering": ("Python", "Flask", "Pydantic", "SQL", "SQLite"),
    "Data Engineering": ("Data Engineering", "Pandas", "Polars", "NumPy", "SQL"),
    "Cloud & Infrastructure": ("AWS", "Docker", "Kubernetes", "Linux"),
    "Systems Programming": ("C++", "CMake", "Linux"),
    "Quality Engineering": ("Testing", "CMake"),
}


def _member_skills(
    domain_skill_names: tuple[str, ...],
    master_profile: MasterSkillProfile,
) -> tuple[MasterSkill, ...]:
    by_name = {skill.name: skill for skill in master_profile.skills}

    return tuple(
        by_name[name] for name in domain_skill_names if name in by_name
    )


def _domain_capability_from_members(
    domain_name: str,
    members: tuple[MasterSkill, ...],
) -> Capability:
    repositories = sorted({repo for skill in members for repo in skill.repositories})
    evidence_count = sum(skill.evidence_count for skill in members)

    confidence = round(
        sum(skill.confidence for skill in members) / len(members),
        4,
    )

    level, _ = classify_capability_level(
        confidence=confidence,
        evidence_count=evidence_count,
        repository_count=len(repositories),
    )

    evidence = tuple(
        CapabilityEvidence(repository=repo, verified=False) for repo in repositories
    )

    return Capability(
        name=domain_name,
        skills=(domain_name,) + tuple(skill.name for skill in members),
        confidence=confidence,
        level=level.value,
        evidence=evidence,
        evidence_count=evidence_count,
        repositories=tuple(repositories),
    )


def build_domain_capabilities(
    master_profile: MasterSkillProfile,
    taxonomy: dict[str, tuple[str, ...]] = DOMAIN_TAXONOMY,
) -> tuple[Capability, ...]:
    domains: list[Capability] = []

    for domain_name, domain_skill_names in taxonomy.items():
        members = _member_skills(domain_skill_names, master_profile)

        if not members:
            continue

        domains.append(_domain_capability_from_members(domain_name, members))

    return tuple(domains)


def build_capability_profile_with_domains(
    master_profile: MasterSkillProfile,
    taxonomy: dict[str, tuple[str, ...]] = DOMAIN_TAXONOMY,
) -> CapabilityProfile:
    """
    Union of M1's per-skill capabilities and M2's domain-level capabilities
    in one CapabilityProfile. A job requirement can match on either an exact
    skill name (M1 behavior, unchanged) or a domain name (new, M2).
    """

    skill_level = build_capability_profile(master_profile)
    domain_level = build_domain_capabilities(master_profile, taxonomy)

    return CapabilityProfile(
        repository_count=master_profile.repository_count,
        capabilities=skill_level.capabilities + domain_level,
    )

