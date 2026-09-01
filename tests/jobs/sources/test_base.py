"""Tests for JobSourceAdapter base-class contract."""
from __future__ import annotations

import pytest

from incomeos.jobs.sources.base import JobSourceAdapter


def test_base_adapter_fetch_raises_not_implemented():
    adapter = JobSourceAdapter()
    with pytest.raises(NotImplementedError):
        adapter.fetch()


def test_default_source_name_is_unknown():
    assert JobSourceAdapter.source_name == "unknown"
