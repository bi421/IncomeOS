from incomeos.jobs.fit import JobRequirement, evaluate_job_fit
from incomeos.skills.aggregator import build_master_profile
from incomeos.skills.levels import CapabilityLevel


def capability_profile():
    return {
        "capabilities": [
            {
                "name": "Python Application Development",
                "skills": ["Python"],
                "confidence": 0.95,
                "level": "A",
            },
            {
                "name": "C++ Systems Development",
                "skills": ["C++"],
                "confidence": 0.85,
                "level": "B",
            },
        ]
    }


def test_job_fit_matches_required_capabilities():
    result = evaluate_job_fit(
        job_id="job-1",
        requirements=(
            JobRequirement("Python", CapabilityLevel.B),
            JobRequirement("C++", CapabilityLevel.B),
        ),
        profile=capability_profile(),
    )

    assert result.fit_score == 1.0
    assert result.missing_requirements == ()
    assert set(result.matched_requirements) == {"Python", "C++"}
    assert result.is_qualified


def test_a_capability_satisfies_b_requirement():
    result = evaluate_job_fit(
        job_id="job-2",
        requirements=(JobRequirement("Python", CapabilityLevel.B),),
        profile=capability_profile(),
    )

    assert result.fit_score == 1.0


def test_b_capability_does_not_satisfy_a_requirement():
    result = evaluate_job_fit(
        job_id="job-3",
        requirements=(JobRequirement("C++", CapabilityLevel.A),),
        profile=capability_profile(),
    )

    assert result.fit_score == 0.0
    assert result.missing_requirements == ("C++",)
    assert not result.is_qualified


def test_missing_requirement_is_explained():
    result = evaluate_job_fit(
        job_id="job-4",
        requirements=(JobRequirement("Docker", CapabilityLevel.B),),
        profile=capability_profile(),
    )

    assert result.fit_score == 0.0
    assert "Docker" in result.missing_requirements
    assert any("no capability evidence" in reason for reason in result.reasons)


def test_empty_requirements_are_not_automatically_a_perfect_fit():
    result = evaluate_job_fit(
        job_id="job-5",
        requirements=(),
        profile=capability_profile(),
    )

    assert result.fit_score == 0.0
    assert not result.is_qualified


def test_skill_matching_is_case_and_whitespace_insensitive():
    result = evaluate_job_fit(
        job_id="job-6",
        requirements=(JobRequirement("  PYTHON  ", CapabilityLevel.B),),
        profile=capability_profile(),
    )

    assert result.fit_score == 1.0
    assert result.matched_requirements == ("  PYTHON  ",)
    assert result.missing_requirements == ()


def test_common_python_alias_matches_without_fuzzy_matching():
    result = evaluate_job_fit(
        job_id="job-7",
        requirements=(JobRequirement("Python 3", CapabilityLevel.B),),
        profile=capability_profile(),
    )

    assert result.fit_score == 1.0
    assert result.matched_requirements == ("Python 3",)


def test_master_skill_profile_matches_job_requirements(github_repos_fixture):
    profile = build_master_profile(github_repos_fixture)

    result = evaluate_job_fit(
        job_id="real-job-1",
        requirements=(
            JobRequirement("Python", CapabilityLevel.B),
            JobRequirement("Docker", CapabilityLevel.B),
        ),
        profile=profile,
    )

    assert "Python" in result.matched_requirements
    assert "Docker" in result.matched_requirements
    assert result.missing_requirements == ()
    assert result.fit_score == 1.0
