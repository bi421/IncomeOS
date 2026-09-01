"""Tests for ArbeitnowSource relevance filtering.

Verifies that jobs not matching IncomeOS focus skills — e.g.
"Director, Regulatory Consultant" — are filtered out by is_relevant().
"""
from __future__ import annotations

import json
from typing import List
from unittest import mock

from incomeos.jobs.models.job import Job
from incomeos.jobs.sources.arbeitnow import ArbeitnowSource


def _make_api_payload(records: List[dict]) -> bytes:
    """Simulate a JSON response body from the Arbeitnow API."""
    return json.dumps({"data": records}).encode("utf-8")


def _fetch_with_mock(records: List[dict]) -> List[Job]:
    """Run ArbeitnowSource.fetch with a mocked HTTP response."""
    mock_resp = mock.MagicMock()
    mock_resp.read.return_value = _make_api_payload(records)
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False

    with mock.patch(
        "incomeos.jobs.sources.arbeitnow.urllib.request.urlopen",
        return_value=mock_resp,
    ):
        return list(ArbeitnowSource().fetch())


def test_director_regulatory_consultant_is_filtered_out():
    """Non-technical titles must NOT pass the relevance filter."""
    records = [
        {
            "id": 1,
            "title": "Director, Regulatory Consultant",
            "url": "https://example.com/job/1",
            "company_name": "Regulatory Corp",
            "description": "Oversee regulatory compliance and strategic planning.",
            "tags": ["compliance", "management"],
            "created_at": 1700000000,
        },
        {
            "id": 2,
            "title": "Python Backend Engineer",
            "url": "https://example.com/job/2",
            "company_name": "Tech Corp",
            "description": "Remote Python position building APIs.",
            "tags": ["python", "backend"],
            "created_at": 1700000001,
        },
    ]

    results = _fetch_with_mock(records)
    titles = [job.title for job in results]

    # Non-technical job must be excluded
    assert "Director, Regulatory Consultant" not in titles
    # Relevant technical job must pass through
    assert "Python Backend Engineer" in titles
    assert len(results) == 1


def test_docker_job_is_relevant():
    """A Docker-focused job should pass through the filter."""
    records = [
        {
            "id": 3,
            "title": "Docker Infrastructure Engineer",
            "url": "https://example.com/job/3",
            "company_name": "CloudOps Inc",
            "description": "Manage Docker containers and Kubernetes clusters.",
            "tags": ["docker", "devops"],
            "created_at": 1700000002,
        },
    ]

    results = _fetch_with_mock(records)
    titles = [job.title for job in results]

    assert "Docker Infrastructure Engineer" in titles
    assert len(results) == 1
