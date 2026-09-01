"""Forensic audit for REAL JOB DATA PIPELINE.

This module does not discover jobs and does not apply to jobs.
It verifies pipeline artifacts and evidence integrity.
"""

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class AuditResult:
    """Result of a pipeline audit."""

    passed: bool
    findings: tuple[str, ...]


def audit_required_fields(
    fields: Iterable[str],
    required: Iterable[str],
) -> AuditResult:
    """Verify that required fields exist."""

    available = set(fields)
    missing = tuple(
        field for field in required
        if field not in available
    )

    if missing:
        return AuditResult(
            passed=False,
            findings=tuple(f"Missing field: {field}" for field in missing),
        )

    return AuditResult(
        passed=True,
        findings=(),
    )
