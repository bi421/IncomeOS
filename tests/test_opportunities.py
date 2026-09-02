from incomeos.opportunities.engine import (
    DEFAULT_OPPORTUNITIES,
    IncomeOpportunity,
    match_opportunities,
)
from incomeos.skills.levels import CapabilityLevel


def profile(*skills):
    return {
        "skills": [
            {
                "name": name,
                "confidence": confidence,
            }
            for name, confidence in skills
        ]
    }


def capability_profile(
    *,
    name="Python Application Development",
    skills=("Python",),
    confidence=0.9,
    level=CapabilityLevel.A,
):
    return {
        "capabilities": [
            {
                "name": name,
                "skills": list(skills),
                "confidence": confidence,
                "level": level.value,
            }
        ]
    }


def test_empty_profile_produces_zero_readiness():
    matches = match_opportunities(profile())

    assert matches
    assert all(
        item.readiness == 0.0
        for item in matches
    )


def test_python_and_testing_match_automation():
    matches = match_opportunities(
        profile(
            ("Python", 1.0),
            ("Testing", 1.0),
        )
    )

    automation = next(
        item
        for item in matches
        if item.opportunity.name == "Python Automation"
    )

    assert automation.readiness == 1.0
    assert set(automation.matched_skills) == {
        "Python",
        "Testing",
    }
    assert automation.missing_skills == ()
    assert automation.readiness_basis == "skill_confidence"


def test_missing_skill_reduces_readiness():
    matches = match_opportunities(
        profile(
            ("Python", 1.0),
        )
    )

    data_engineering = next(
        item
        for item in matches
        if item.opportunity.name == "Data Engineering Support"
    )

    assert 0.0 < data_engineering.readiness < 1.0
    assert "Data Engineering" in data_engineering.missing_skills


def test_cplusplus_opportunity_requires_multiple_skills():
    matches = match_opportunities(
        profile(
            ("C++", 0.9),
            ("Python", 0.8),
            ("Testing", 0.9),
        )
    )

    quant = next(
        item
        for item in matches
        if item.opportunity.name
        == "C++ Quant / Performance Engineering"
    )

    assert quant.readiness > 0.8
    assert quant.missing_skills == ()


def test_results_are_sorted_by_score():
    matches = match_opportunities(
        profile(
            ("Python", 1.0),
            ("Testing", 1.0),
            ("Data Engineering", 1.0),
        )
    )

    scores = [
        item.opportunity_score
        for item in matches
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )


def test_custom_opportunity_is_supported():
    custom = IncomeOpportunity(
        name="Custom Python Work",
        description="Custom opportunity.",
        required_skills=("Python",),
        skill_weights=(1.0,),
        base_value=0.8,
        difficulty=0.4,
    )

    matches = match_opportunities(
        profile(("Python", 0.75)),
        opportunities=(custom,),
    )

    assert len(matches) == 1
    assert matches[0].readiness == 0.75
    assert matches[0].opportunity.name == "Custom Python Work"


def test_all_default_opportunities_are_valid():
    assert len(DEFAULT_OPPORTUNITIES) == 5

    for opportunity in DEFAULT_OPPORTUNITIES:
        assert opportunity.name
        assert opportunity.required_skills
        assert len(opportunity.required_skills) == len(
            opportunity.skill_weights
        )


def test_a_capability_preserves_high_confidence():
    matches = match_opportunities(
        capability_profile(
            confidence=0.92,
            level=CapabilityLevel.A,
        ),
        opportunities=(
            IncomeOpportunity(
                name="Python Work",
                description="Python work",
                required_skills=("Python",),
                skill_weights=(1.0,),
                base_value=1.0,
                difficulty=0.0,
            ),
        ),
    )

    assert matches[0].readiness == 0.92
    assert (
        matches[0].readiness_basis
        == "capability_level_and_evidence_confidence"
    )


def test_b_capability_is_not_treated_as_full_a_readiness():
    matches = match_opportunities(
        capability_profile(
            confidence=0.95,
            level=CapabilityLevel.B,
        ),
        opportunities=(
            IncomeOpportunity(
                name="Python Work",
                description="Python work",
                required_skills=("Python",),
                skill_weights=(1.0,),
                base_value=1.0,
                difficulty=0.0,
            ),
        ),
    )

    assert matches[0].readiness == 0.70


def test_unknown_capability_produces_no_readiness():
    matches = match_opportunities(
        capability_profile(
            confidence=1.0,
            level=CapabilityLevel.UNKNOWN,
        ),
        opportunities=(
            IncomeOpportunity(
                name="Python Work",
                description="Python work",
                required_skills=("Python",),
                skill_weights=(1.0,),
                base_value=1.0,
                difficulty=0.0,
            ),
        ),
    )

    assert matches[0].readiness == 0.0
    assert matches[0].missing_skills == ("Python",)
