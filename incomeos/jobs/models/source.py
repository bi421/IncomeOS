"""Job source metadata."""

from dataclasses import dataclass


@dataclass(frozen=True)
class JobSource:
    """Identifies where a job was discovered."""

    name: str
    url: str
    trust_level: str
