
from incomeos.decision.job_decision import (
    normalise_job_requirements,
    persist_job_decision,
)
from incomeos.decision.persistence import DecisionStore
from incomeos.skills.levels import CapabilityLevel


def profile():
    return {
        "capabilities": [
            {
                "name": "Python Application Development",
                "skills": ["Python"],
                "confidence": 0.95,
                "level": "A",
            },
            {
                "name": "Testing",
                "skills": ["Testing"],
                "confidence": 0.85,
                "level": "B",
            },
        ]
    }


def test_job_requirements_normalise_simple_skill_list():
    job = {
        "id": 101,
        "required_skills": [
            "Python",
            "Testing",
        ],
    }

    requirements = normalise_job_requirements(
        job
    )

    assert requirements == (
        requirements[0],
        requirements[1],
    )
    assert requirements[0].skill == "Python"
    assert requirements[0].minimum_level is CapabilityLevel.B
    assert requirements[1].skill == "Testing"


def test_job_requirements_support_explicit_level():
    job = {
        "id": 102,
        "requirements": [
            {
                "skill": "Python",
                "minimum_level": "A",
            },
            {
                "skill": "Testing",
                "minimum_level": "B",
            },
        ],
    }

    requirements = normalise_job_requirements(
        job
    )

    assert requirements[0].minimum_level is CapabilityLevel.A
    assert requirements[1].minimum_level is CapabilityLevel.B


def test_concrete_job_is_persisted_with_real_job_id(
    tmp_path,
):
    store = DecisionStore(
        tmp_path / "decisions.db"
    )

    job = {
        "id": 5001,
        "title": "Python Automation Engineer",
        "company": "Example Co",
        "required_skills": [
            "Python",
            "Testing",
        ],
    }

    result = persist_job_decision(
        job=job,
        opportunity_name="Python Automation",
        profile=profile(),
        store=store,
    )

    assert result.job_id == "5001"
    assert result.fit.job_id == "5001"
    assert result.fit.fit_score == 1.0
    assert result.decision.decision == "APPLY"

    loaded = store.get(
        result.decision.decision_id
    )

    assert loaded is not None
    assert loaded.job_id == "5001"
    assert loaded.opportunity_name == "Python Automation"
    assert loaded.decision == "APPLY"

    snapshot = loaded.evidence_snapshot[0]

    assert snapshot["job_id"] == "5001"
    assert snapshot["job_title"] == "Python Automation Engineer"
    assert snapshot["company"] == "Example Co"


def test_missing_job_requirement_causes_review(
    tmp_path,
):
    store = DecisionStore(
        tmp_path / "decisions.db"
    )

    job = {
        "id": 5002,
        "title": "Python + Docker Engineer",
        "company": "Example Co",
        "required_skills": [
            "Python",
            "Docker",
        ],
    }

    result = persist_job_decision(
        job=job,
        opportunity_name="Docker Deployment Support",
        profile=profile(),
        store=store,
    )

    assert result.fit.fit_score == 0.5
    assert result.fit.missing_requirements == (
        "Docker",
    )
    assert result.decision.decision == "REVIEW"


def test_a_requirement_rejects_b_capability(
    tmp_path,
):
    store = DecisionStore(
        tmp_path / "decisions.db"
    )

    job = {
        "id": 5003,
        "title": "Testing Lead",
        "company": "Example Co",
        "requirements": [
            {
                "skill": "Testing",
                "minimum_level": "A",
            },
        ],
    }

    result = persist_job_decision(
        job=job,
        opportunity_name="Automated Testing",
        profile=profile(),
        store=store,
    )

    assert result.fit.fit_score == 0.0
    assert result.fit.missing_requirements == (
        "Testing",
    )
    assert result.decision.decision == "REVIEW"


def test_title_does_not_create_seniority_requirement():
    job = {
        "id": 5004,
        "title": "Senior Python Engineer",
        "required_skills": ["Python"],
    }

    requirements = normalise_job_requirements(
        job
    )

    assert len(requirements) == 1
    assert requirements[0].skill == "Python"
    assert requirements[0].minimum_level is CapabilityLevel.B
