import pytest

from incomeos.capabilities.domains import (
    DOMAIN_TAXONOMY,
    build_capability_profile_with_domains,
    build_domain_capabilities,
)
from incomeos.jobs.fit import JobRequirement, evaluate_job_fit
from incomeos.jobs.requirements import parse_job_record
from incomeos.skills.aggregator import MasterSkill, MasterSkillProfile
from incomeos.skills.levels import CapabilityLevel


# --- requirements.py bug fix -------------------------------------------------

def test_string_job_id_with_no_raw_data_does_not_raise():
    # Previously raised NameError: name 'legacy_job' is not defined,
    # because job_id is not a dict so `legacy_job` was never assigned.
    result = parse_job_record("job-42", raw_data=None)

    assert result.job_id == "job-42"
    assert result.required_skills == ()
    assert result.preferred_skills == ()


def test_string_job_id_with_raw_data_still_works():
    raw = repr({"description": "Required Skills: Python, Docker"})

    result = parse_job_record("job-99", raw_data=raw)

    assert result.job_id == "job-99"
    assert "Python" in result.required_skills
    assert "Docker" in result.required_skills


def test_legacy_dict_job_id_behavior_is_unchanged():
    result = parse_job_record({"id": 7, "title": "Legacy"}, raw_data=None)

    assert result.job_id == "7"
    assert result.title == "Legacy"
    assert result.required_skills == ()


# --- M2 domain capabilities ---------------------------------------------------

def _profile_with(*skills: MasterSkill) -> MasterSkillProfile:
    return MasterSkillProfile(
        repository_count=len({r for s in skills for r in s.repositories}),
        skill_record_count=sum(s.evidence_count for s in skills),
        skills=skills,
    )


def test_domain_only_appears_when_a_member_skill_has_evidence():
    profile = _profile_with(
        MasterSkill(
            name="Python",
            confidence=0.9,
            evidence_count=3,
            repositories=("repo-a", "repo-b"),
        )
    )

    domains = build_domain_capabilities(profile)
    domain_names = {d.name for d in domains}

    assert "Backend Engineering" in domain_names
    assert "Systems Programming" not in domain_names  # no C++/CMake/Linux evidence


def test_domain_capability_aggregates_member_evidence():
    profile = _profile_with(
        MasterSkill(
            name="Python",
            confidence=0.9,
            evidence_count=2,
            repositories=("repo-a",),
        ),
        MasterSkill(
            name="SQL",
            confidence=0.7,
            evidence_count=1,
            repositories=("repo-b",),
        ),
    )

    domains = build_domain_capabilities(profile)
    backend = next(d for d in domains if d.name == "Backend Engineering")

    assert set(backend.skills) == {"Backend Engineering", "Python", "SQL"}
    assert backend.evidence_count == 3
    assert set(backend.repositories) == {"repo-a", "repo-b"}
    assert backend.confidence == pytest.approx((0.9 + 0.7) / 2, abs=1e-4)


def test_capability_profile_with_domains_matches_on_domain_name():
    profile = _profile_with(
        MasterSkill(
            name="Python",
            confidence=0.95,
            evidence_count=3,
            repositories=("repo-a", "repo-b"),
        ),
        MasterSkill(
            name="SQL",
            confidence=0.9,
            evidence_count=2,
            repositories=("repo-a", "repo-b"),
        ),
    )

    capability_profile = build_capability_profile_with_domains(profile)

    result = evaluate_job_fit(
        job_id="m2-job-1",
        requirements=(JobRequirement("Backend Engineering", CapabilityLevel.B),),
        profile=capability_profile,
    )

    assert result.fit_score == 1.0
    assert result.matched_requirements == ("Backend Engineering",)


def test_capability_profile_with_domains_still_matches_on_skill_name():
    # M1 behavior (matching by exact skill name) must survive unchanged
    # after adding the domain layer on top.
    profile = _profile_with(
        MasterSkill(
            name="Python",
            confidence=0.95,
            evidence_count=3,
            repositories=("repo-a", "repo-b"),
        ),
    )

    capability_profile = build_capability_profile_with_domains(profile)

    result = evaluate_job_fit(
        job_id="m2-job-2",
        requirements=(JobRequirement("Python", CapabilityLevel.B),),
        profile=capability_profile,
    )

    assert result.fit_score == 1.0


def test_all_taxonomy_skill_names_look_plausible():
    # Sanity check on the draft taxonomy itself, not a correctness guarantee â€”
    # just catches obvious typos in DOMAIN_TAXONOMY skill names.
    all_skills = {name for names in DOMAIN_TAXONOMY.values() for name in names}
    assert all(isinstance(name, str) and name.strip() for name in all_skills)

