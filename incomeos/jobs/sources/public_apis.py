from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Iterable

from incomeos.jobs.filters import is_relevant
from incomeos.jobs.models.job import Job
from .base import JobSourceAdapter

_FOCUS_KEYWORDS = tuple(
    alias
    for skill in ("Python", "Docker", "C++", "CMake", "Testing", "Data Engineering")
    for alias in {
        skill.lower(),
        *({"data engineering", "data engineer", "data pipeline", "data pipelines", "etl"} if skill == "Data Engineering" else set()),
    }
)


class JsonApiSource(JobSourceAdapter):
    timeout = 30

    def _get_json(self, url: str) -> Any:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "IncomeOS/1.0 (+https://github.com/bi421/IncomeOS)", "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


class HimalayasSource(JsonApiSource):
    """Free public remote-jobs API; cursor pagination is supported."""

    source_name = "himalayas"
    base_url = "https://himalayas.app/jobs/api"

    def fetch(self) -> Iterable[Job]:
        cursor: str | None = None
        seen: set[str] = set()
        for _ in range(10):
            params = {"limit": "20"}
            if cursor:
                params["cursor"] = cursor
            url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
            payload = self._get_json(url)
            for record in payload.get("jobs", []):
                if not isinstance(record, dict):
                    continue
                title = str(record.get("title", "")).strip()
                link = str(record.get("applicationLink", "")).strip()
                description = str(record.get("description", ""))
                if not title or not link or link in seen:
                    continue
                seen.add(link)
                if not is_relevant(title, description, record.get("categories", []), list(_FOCUS_KEYWORDS)):
                    continue
                yield Job(
                    source=self.source_name,
                    title=title,
                    source_url=link,
                    company=str(record.get("companyName", "")),
                    description=description,
                    created_at=str(record.get("pubDate", "")),
                    raw_data=record,
                )
            cursor = payload.get("nextCursor")
            if not cursor:
                break


class RemotiveSource(JsonApiSource):
    """Remotive public API. Listings are delayed by the provider's terms."""

    source_name = "remotive"
    url = "https://remotive.com/api/remote-jobs"

    def fetch(self) -> Iterable[Job]:
        payload = self._get_json(self.url)
        observed_at = datetime.now(timezone.utc).isoformat()
        for record in payload.get("jobs", []):
            if not isinstance(record, dict):
                continue
            title = str(record.get("title", "")).strip()
            link = str(record.get("url", "")).strip()
            description = str(record.get("description", ""))
            if not title or not link:
                continue
            tags = record.get("tags", []) or [record.get("category", "")]
            if not is_relevant(title, description, tags, list(_FOCUS_KEYWORDS)):
                continue
            yield Job(
                source=self.source_name,
                title=title,
                source_url=link,
                company=str(record.get("company_name", "")),
                description=description,
                created_at=str(record.get("publication_date", "") or observed_at),
                raw_data=record,
            )
