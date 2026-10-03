from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class SourceDescriptor:
    """Static provenance metadata for an enabled public job source."""

    endpoint: str
    protocol: str
    provider_type: str


SOURCE_DESCRIPTORS = {
    "himalayas": SourceDescriptor(
        "https://himalayas.app/jobs/api", "HTTPS JSON API", "remote job board"
    ),
    "remotive": SourceDescriptor(
        "https://remotive.com/api/remote-jobs", "HTTPS JSON API", "remote job board"
    ),
    "remoteok": SourceDescriptor(
        "https://remoteok.com/api", "HTTPS JSON API", "remote job board"
    ),
    "weworkremotely": SourceDescriptor(
        "https://weworkremotely.com/remote-jobs.rss", "HTTPS RSS", "remote job board"
    ),
}


def descriptor_for(source: str) -> SourceDescriptor:
    """Return known provenance metadata; unknown adapters remain explicitly unclassified."""
    return SOURCE_DESCRIPTORS.get(
        source,
        SourceDescriptor("", "unknown", "unclassified"),
    )


def observed_now() -> str:
    return datetime.now(timezone.utc).isoformat()
