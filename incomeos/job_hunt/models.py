from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceHealth:
    """Observed result of one real job source during a hunt."""

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
        """Fraction of fetched records that survived IncomeOS validation."""
        if self.fetched == 0:
            return 0.0
        return self.accepted / self.fetched


@dataclass(frozen=True)
class HuntItem:
    """A persisted real job with deterministic candidate-fit evidence."""

    job_id: str
    source: str
    title: str
    company: str
    url: str
    location: str
    description: str
    fit_score: float
    matched_skills: tuple[str, ...]
    missing_skills: tuple[str, ...]


@dataclass(frozen=True)
class HuntReport:
    """Complete result of one bounded job-hunt run."""

    items: tuple[HuntItem, ...]
    sources: tuple[SourceHealth, ...]

    @property
    def failed_sources(self) -> tuple[str, ...]:
        return tuple(x.source for x in self.sources if x.failed)

    @property
    def total_fetched(self) -> int:
        return sum(x.fetched for x in self.sources)
