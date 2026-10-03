from incomeos.job_hunt.eligibility import assess_eligibility
from incomeos.jobs.models.job import Job


def job(description="", **raw):
    return Job("test", "Python Developer", "https://example.com/job/1", "Example", description, raw_data=raw)


def test_generic_remote_is_unknown_not_proof_of_mongolia_access():
    result = assess_eligibility(job("Remote Python developer"), "Mongolia")
    assert result.status == "UNKNOWN"


def test_worldwide_is_pass():
    result = assess_eligibility(job("Work from anywhere in the world"), "Mongolia")
    assert result.status == "PASS"


def test_explicit_mongolia_is_pass():
    result = assess_eligibility(
        job("", candidate_required_location=["Mongolia"]), "Mongolia"
    )
    assert result.status == "PASS"


def test_worldwide_exception_for_mongolia_is_fail():
    result = assess_eligibility(
        job("Worldwide except Mongolia"), "Mongolia"
    )
    assert result.status == "FAIL"


def test_us_only_is_fail():
    result = assess_eligibility(
        job("", candidate_required_location=["United States only"]), "Mongolia"
    )
    assert result.status == "FAIL"
