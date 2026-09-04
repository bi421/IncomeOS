"""Canonical skill vocabulary.

There used to be three separate hardcoded skill-keyword lists spread
across incomeos/jobs/matching/matcher.py, incomeos/insights/analyzer.py,
and incomeos/job_analyzer/analyzer.py (now deleted) - each slightly
different, so the same job could score differently depending on which
module happened to touch it. One list, one place.
"""

from __future__ import annotations

SKILL_VOCAB: tuple[str, ...] = (
    "python", "java", "javascript", "typescript", "c++", "go", "rust",
    "react", "vue", "angular", "node", "django", "flask", "fastapi",
    "docker", "kubernetes", "aws", "azure", "gcp",
    "sql", "postgresql", "mysql", "mongodb", "redis",
    "machine learning", "data engineering", "devops", "ci/cd",
    "testing", "api", "microservices", "git", "linux", "cmake",
)