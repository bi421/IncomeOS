from incomeos.jobs.deduplication.deduplicator import deduplicate_jobs
from incomeos.jobs.models.job import Job
from incomeos.jobs.normalization.normalizer import normalize_job


def test_normalize_mapping_canonicalizes_url():
    job = normalize_job(
        {
            "source": " fake ",
            "title": " Python ",
            "url": "HTTPS://EXAMPLE.COM/job/1#section",
            "company": " Example ",
            "description": "desc",
            "raw_data": {"location": "Worldwide"},
        }
    )

    assert job.source == "fake"
    assert job.title == "Python"
    assert job.source_url == "https://example.com/job/1"
    assert job.company == "Example"
    assert job.raw_data["location"] == "Worldwide"


def test_deduplicate_jobs_uses_canonical_url():
    jobs = [
        Job("a", "One", "https://EXAMPLE.com/job/1#x"),
        Job("b", "Duplicate", "https://example.com/job/1"),
        Job("c", "Two", "https://example.com/job/2"),
    ]

    result = deduplicate_jobs(jobs)

    assert [job.title for job in result] == ["One", "Two"]
