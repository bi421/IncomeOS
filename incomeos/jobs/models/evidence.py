"""Evidence attached to a discovered job."""

from dataclasses import dataclass


@dataclass(frozen=True)
class JobEvidence:
    """Evidence supporting the existence/status of a job."""

    source: str
    source_url: str
    observed_at: str
    status: str
    evidence_type: str
