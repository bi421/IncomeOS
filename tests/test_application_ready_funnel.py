from incomeos.applications.generator import EvidenceBoundGenerator
from incomeos.job_hunt.application_queue import ApplicationQueue
from incomeos.job_hunt.eligibility import assess_eligibility
from incomeos.jobs.models.job import Job


def test_remote_job_is_application_eligible_and_prepared(tmp_path):
    job = Job(
        source="fixture",
        title="Python Automation Engineer",
        source_url="https://example.com/jobs/1",
        company="Example",
        description="Remote worldwide role using Python and Testing.",
        raw_data={"location": "Worldwide"},
    )
    eligibility = assess_eligibility(job, "Mongolia")
    assert eligibility.status == "PASS"

    profile = tmp_path / "profile.json"
    profile.write_text(
        '{"skills":[{"name":"Python"}],"verified_evidence":[]}',
        encoding="utf-8",
    )
    queue = ApplicationQueue(tmp_path / "queue.db")
    prepared = queue.prepare(
        job=job,
        fit_score=0.82,
        eligibility=eligibility,
        generator=EvidenceBoundGenerator(profile),
    )
    assert prepared is not None
    assert prepared.status == "READY"
    assert queue.status(job.source_url) == "READY"


def test_restricted_job_is_not_prepared(tmp_path):
    job = Job(
        source="fixture",
        title="Python Engineer",
        source_url="https://example.com/jobs/2",
        description="Remote, US only. Must be located in the United States.",
    )
    eligibility = assess_eligibility(job, "Mongolia")
    assert eligibility.status == "FAIL"
    queue = ApplicationQueue(tmp_path / "queue.db")
    profile = tmp_path / "profile.json"
    profile.write_text('{"skills":[],"verified_evidence":[]}', encoding="utf-8")
    assert queue.prepare(
        job=job,
        fit_score=0.95,
        eligibility=eligibility,
        generator=EvidenceBoundGenerator(profile),
    ) is None


def test_citizenship_restriction_fails_closed(tmp_path):
    job = Job(
        source="fixture",
        title="Software Engineer",
        source_url="https://example.com/jobs/4",
        description="Remote - USA. This position requires US citizenship.",
    )
    eligibility = assess_eligibility(job, "Mongolia")
    assert eligibility.status == "FAIL"


def test_unknown_eligibility_fails_closed(tmp_path):
    job = Job(
        source="fixture",
        title="Python Engineer",
        source_url="https://example.com/jobs/3",
        description="Python engineering role.",
    )
    eligibility = assess_eligibility(job, "Mongolia")
    assert eligibility.status == "UNKNOWN"
    profile = tmp_path / "profile.json"
    profile.write_text('{"skills":[],"verified_evidence":[]}', encoding="utf-8")
    queue = ApplicationQueue(tmp_path / "queue.db")
    assert queue.prepare(
        job=job,
        fit_score=0.95,
        eligibility=eligibility,
        generator=EvidenceBoundGenerator(profile),
    ) is None


def test_himalayas_location_restriction_fails_for_mongolia():
    job = Job(
        source="himalayas",
        title="Python Engineer",
        source_url="https://example.com/jobs/5",
        description="Remote engineering role using Python.",
        raw_data={"locationRestrictions": ["Romania"]},
    )
    result = assess_eligibility(job, "Mongolia")
    assert result.status == "FAIL"
    assert "locationRestrictions" in result.reason


def test_remotive_allowed_location_fails_when_mongolia_is_absent():
    job = Job(
        source="remotive",
        title="Python Engineer",
        source_url="https://example.com/jobs/6",
        description="Remote engineering role using Python.",
        raw_data={"candidate_required_location": "Europe, USA, UK, Canada"},
    )
    result = assess_eligibility(job, "Mongolia")
    assert result.status == "FAIL"


def test_remotive_worldwide_passes():
    job = Job(
        source="remotive",
        title="Python Engineer",
        source_url="https://example.com/jobs/7",
        description="Remote engineering role using Python.",
        raw_data={"candidate_required_location": "Worldwide"},
    )
    result = assess_eligibility(job, "Mongolia")
    assert result.status == "PASS"


def test_weworkremotely_worldwide_region_passes():
    job = Job(
        source="weworkremotely",
        title="Python Engineer",
        source_url="https://example.com/jobs/8",
        description="Engineering role using Python.",
        raw_data={"region": "Anywhere in the World"},
    )
    result = assess_eligibility(job, "Mongolia")
    assert result.status == "PASS"
