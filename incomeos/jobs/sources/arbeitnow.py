from __future__ import annotations
import json
import urllib.request
from datetime import datetime, timezone
from typing import Iterable

from incomeos.jobs.models.job import Job
from incomeos.jobs.filters import is_relevant
from .base import JobSourceAdapter

def _safe_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

class ArbeitnowSource(JobSourceAdapter):
    source_name = "arbeitnow"

    def fetch(self) -> Iterable[Job]:
        url = "https://www.arbeitnow.com/api/job-board-api"
        req = urllib.request.Request(url, headers={"User-Agent": "IncomeOS/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        observed_at = datetime.now(timezone.utc).isoformat()
        for record in payload.get("data", []):
            if not is_relevant(
                record.get("title", ""),
                record.get("description", ""),
                record.get("tags", []),
            ):
                continue
            ts = _safe_int(record.get("created_at"))
            created_at = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else observed_at
            yield Job(
                source=self.source_name,
                title=record.get("title", "Untitled"),
                source_url=record.get("url", ""),
                company=record.get("company_name", ""),
                description=record.get("description", ""),
                created_at=created_at,
                raw_data=record,
            )


class ArbeitnowUKSource(ArbeitnowSource):
    """UK feed from the same provider, kept distinct for provenance."""

    source_name = "arbeitnow_uk"
    url = "https://www.arbeitnow.co.uk/api/job-board-api"

    def fetch(self) -> Iterable[Job]:
        req = urllib.request.Request(self.url, headers={"User-Agent": "IncomeOS/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        observed_at = datetime.now(timezone.utc).isoformat()
        for record in payload.get("data", []):
            if not is_relevant(record.get("title", ""), record.get("description", ""), record.get("tags", [])):
                continue
            ts = _safe_int(record.get("created_at"))
            created_at = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else observed_at
            yield Job(
                source=self.source_name,
                title=record.get("title", "Untitled"),
                source_url=record.get("url", ""),
                company=record.get("company_name", ""),
                description=record.get("description", ""),
                created_at=created_at,
                raw_data=record,
            )
