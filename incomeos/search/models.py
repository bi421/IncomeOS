from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchDocument:
    repository: str
    path: str
    language: str
    category: str
    content: str


@dataclass(frozen=True)
class SearchResult:
    repository: str
    path: str
    language: str
    category: str
    score: float
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class AuditFinding:
    severity: str
    category: str
    message: str
    repository: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class AuditReport:
    repository_count: int
    document_count: int
    finding_count: int
    findings: tuple[AuditFinding, ...]

    @property
    def critical_count(self) -> int:
        return sum(f.severity == "critical" for f in self.findings)

    @property
    def warning_count(self) -> int:
        return sum(f.severity == "warning" for f in self.findings)

    @property
    def info_count(self) -> int:
        return sum(f.severity == "info" for f in self.findings)
