from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SourceRunResult:
    source: str
    fetched: int
    validated: int
    inserted: int
    existing: int
    skipped: int
    failed: bool
    error: str | None = None

@dataclass(frozen=True)
class PipelineRunResult:
    sources: tuple[SourceRunResult, ...]
    total_fetched: int
    total_validated: int
    total_inserted: int
    total_existing: int
    total_skipped: int
    total_failed: int
