from datetime import datetime, timezone

from incomeos.job_hunt.scoring import score_job
from incomeos.jobs.models.job import Job


def _job(**kwargs):
    values = {
        "source": "test",
        "title": "Senior Python Data Engineer",
        "source_url": "https://example.com/jobs/1",
        "company": "Example",
        "description": "Senior Python Data Engineer. Remote worldwide.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "raw_data": {
            "candidate_required_location": "Worldwide",
            "employment_type": "Full-time",
            "salary": "$100,000-$130,000",
        },
    }
    values.update(kwargs)
    return Job(**values)


def test_job_score_awards_only_explicit_evidence():
    result = score_job(
        _job(),
        matched_skills=("Python", "Data Engineering"),
        requested_skill_count=6,
        eligibility_reason="candidate_required_location explicitly permits the target country",
    )

    assert result.overall_score == 73
    assert {x.name: x.points for x in result.components} == {
        "skill_match": 13,
        "location_eligibility": 20,
        "role_relevance": 15,
        "seniority_evidence": 10,
        "employment_type_evidence": 5,
        "compensation_evidence": 5,
        "freshness": 5,
    }
    assert result.warnings == ()


def test_job_score_does_not_invent_missing_salary_or_metadata():
    result = score_job(
        _job(
            title="Python Developer",
            description="Build APIs with Python.",
            created_at="",
            raw_data={"candidate_required_location": "Mongolia"},
        ),
        matched_skills=("Python",),
        requested_skill_count=6,
        eligibility_reason="target country appears in the job location",
    )

    assert result.overall_score == 42
    assert "salary/compensation is unknown" in result.warnings
    assert "employment type is unknown" in result.warnings
    assert "seniority compatibility is unknown" in result.warnings
    assert "job freshness is unknown or the listing is older than 90 days" in result.warnings


def test_job_score_never_exceeds_100():
    result = score_job(
        _job(),
        matched_skills=("Python", "Testing", "Data Engineering", "C++", "Docker", "CMake"),
        requested_skill_count=6,
        eligibility_reason="worldwide eligibility is explicitly stated",
    )
    assert result.overall_score == 100
