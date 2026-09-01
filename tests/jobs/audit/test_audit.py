"""Tests for incomeos.jobs.audit.audit_required_fields."""
from __future__ import annotations

from incomeos.jobs.audit.audit import AuditResult, audit_required_fields


def test_all_required_fields_present():
    result = audit_required_fields(
        fields=["title", "url", "company", "description"],
        required=["title", "url"],
    )
    assert result.passed is True
    assert result.findings == ()


def test_missing_single_required_field():
    result = audit_required_fields(
        fields=["title", "company"],
        required=["title", "url"],
    )
    assert result.passed is False
    assert len(result.findings) == 1
    assert result.findings[0] == "Missing field: url"


def test_multiple_missing_fields():
    result = audit_required_fields(
        fields=["title"],
        required=["title", "url", "company"],
    )
    assert result.passed is False
    assert len(result.findings) == 2
    assert "Missing field: url" in result.findings
    assert "Missing field: company" in result.findings


def test_no_fields_present():
    result = audit_required_fields(
        fields=[],
        required=["title"],
    )
    assert result.passed is False
    assert "Missing field: title" in result.findings


def test_returns_audit_result_instance():
    result = audit_required_fields(fields=["a"], required=["a"])
    assert isinstance(result, AuditResult)
