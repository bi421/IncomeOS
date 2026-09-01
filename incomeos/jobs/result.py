from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SourceRunResult:
    source: str
    fetched: int
    inserted: int
    existing: int
    failed: bool
    error: str | None = None
    validated: int = 0
    skipped: int = 0