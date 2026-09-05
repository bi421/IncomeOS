from __future__ import annotations
import json
import urllib.request
from datetime import datetime, timezone
from typing import Iterable

from incomeos.jobs.models.job import Job
from .base import JobSourceAdapter

def _safe_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

class RemoteOKSource(JobSourceAdapter):
    source_name = "remoteok"

    def fetch(self) -> Iterable[Job]:
        url = "https://remoteok.com/api"
        req = urllib.request.Request(url, headers={"User-Agent": "IncomeOS/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        observed_at = datetime.now(timezone.utc).isoformat()
        for record in payload:
            if not isinstance(record, dict):
                continue
            position = str(record.get("position", "")).strip()
            if position.lower() in {"legal notice", "legal disclaimer"}:
                continue
            ts = _safe_int(record.get("epoch"))
            created_at = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else observed_at
            yield Job(
                source=self.source_name,
                title=position or "Untitled",
                source_url=record.get("url", ""),
                company=record.get("company", ""),
                description=record.get("description", ""),
                created_at=created_at,
                raw_data=record,
            )
