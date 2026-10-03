from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceHealth:
    source: str
    fetched: int
    accepted: int
    failed: bool
    error: str = ""
    endpoint: str = ""
    protocol: str = "unknown"
    provider_type: str = "unclassified"
    observed_at: str = ""

    @property
    def acceptance_rate(self) -> float:
        if self.fetched == 0:
            return 0.0
        return self.accepted / self.fetched


@dataclass(frozen=True)
class HuntItem:
    job_id: str
    source: str
    title: str
    company: str
    url: str
    location: str
    description: str
    fit_score: float
    overall_score: int
    score_breakdown: tuple[dict[str, Any], ...]
    score_warnings: tuple[str, ...]
    matched_skills: tuple[str, ...]
    missing_skills: tuple[str, ...]
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HuntReport:
    items: tuple[HuntItem, ...]
    sources: tuple[SourceHealth, ...]

    @property
    def failed_sources(self) -> tuple[str, ...]:
        return tuple(x.source for x in self.sources if x.failed)

    @property
    def total_fetched(self) -> int:
        return sum(x.fetched for x in self.sources)
