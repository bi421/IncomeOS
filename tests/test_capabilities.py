from incomeos.capabilities.models import (
    Capability,
    build_capability_profile,
    capability_from_master_skill,
)
from incomeos.jobs.fit import JobRequirement, evaluate_job_fit
from incomeos.skills.aggregator import MasterSkill, MasterSkillProfile
from incomeos.skills.levels import CapabilityLevel


def _master_skill(**overrides) -> MasterSkill:
    defaults = dict(
        name="Python",
        confidence=0.95,
        evidence_count=3,
        repositories=("repo-a", "repo-b"),
        verified_evidence_count=0,
        verified_decision_ids=(),
    )
    defaults.update(overrides)
    return MasterSkill(**defaults)


def test_capability_from_master_skill_is_1_to_1():
    skill = _master_skill()

    capability = capability_from_master_skill(skill)

    assert capability.name == "Python"
    assert capability.skills == ("Python",)
    assert capability.confidence == skill.confidence
    assert capability.level == CapabilityLevel.A.value
    assert capability.repositories == skill.repositories


def test_capability_level_matches_classify_capability_level():
    weak_skill = _master_skill(
        name="Rust",
        confidence=0.60,
        evidence_count=1,
        repositories=("repo-a",),
    )

    capability = capability_from_master_skill(weak_skill)

    assert capability.level == CapabilityLevel.B.value


def test_capability_evidence_includes_verified_decisions():
    skill = _master_skill(
        verified_evidence_count=1,
        verified_decision_ids=("dec-123",),
    )

    capability = capability_from_master_skill(skill)

    verified = [item for item in capability.evidence if item.verified]

    assert len(verified) == 1
    assert verified[0].decision_id == "dec-123"


def test_build_capability_profile_preserves_repository_count():
    profile = MasterSkillProfile(
        repository_count=4,
        skill_record_count=10,
        skills=(_master_skill(),),
    )

    capability_profile = build_capability_profile(profile)

    assert capability_profile.repository_count == 4
    assert len(capability_profile.capabilities) == 1
    assert isinstance(capability_profile.capabilities[0], Capability)


def test_capability_profile_is_backward_compatible_with_job_fit():
    profile = MasterSkillProfile(
        repository_count=2,
        skill_record_count=5,
        skills=(
            _master_skill(name="Python"),
            _master_skill(
                name="Docker",
                confidence=0.55,
                evidence_count=1,
                repositories=("repo-a",),
            ),
        ),
    )

    capability_profile = build_capability_profile(profile)

    result = evaluate_job_fit(
        job_id="m1-job-1",
        requirements=(
            JobRequirement("Python", CapabilityLevel.B),
            JobRequirement("Docker", CapabilityLevel.B),
        ),
        profile=capability_profile,
    )

    assert result.matched_requirements == ("Python", "Docker") or set(
        result.matched_requirements
    ) == {"Python", "Docker"}
    assert result.missing_requirements == ()
    assert result.fit_score == 1.0

