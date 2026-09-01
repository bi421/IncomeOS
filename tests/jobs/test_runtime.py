"""Tests for real job ingestion."""

from incomeos.jobs.models.job import Job
from incomeos.jobs.runtime.runner import _valid_job


def test_valid_job_requires_identity_fields():
    job = Job(
        title="Python Developer",
        company="Example",
        description="Remote Python role.",
        source="test",
        source_url="https://example.com/job/1",
    )

    assert _valid_job(job)


def test_invalid_job_without_title():
    job = Job(
        title="",
        company="Example",
        description="Remote Python role.",
        source="test",
        source_url="https://example.com/job/1",
    )

    assert not _valid_job(job)


def test_invalid_job_without_source_url():
    job = Job(
        title="Python Developer",
        company="Example",
        description="Remote Python role.",
        source="test",
        source_url="",
    )

    assert not _valid_job(job)
