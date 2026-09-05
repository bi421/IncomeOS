"""We Work Remotely RSS source adapter."""

import html
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Iterable

from incomeos.jobs.models.job import Job
from incomeos.jobs.sources.base import JobSourceAdapter


URL = "https://weworkremotely.com/remote-jobs.rss"


def _text(parent: ET.Element, name: str) -> str:
    node = parent.find(name)
    if node is None or node.text is None:
        return ""
    return html.unescape(node.text).strip()


class WeWorkRemotelySource(JobSourceAdapter):
    """Fetch real jobs from We Work Remotely RSS."""

    source_name = "weworkremotely"

    def fetch(self) -> Iterable[Job]:
        request = urllib.request.Request(
            URL,
            headers={
                "User-Agent": "IncomeOS/0.1 (+real-job-data-pipeline)",
            },
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read()

        root = ET.fromstring(body)
        channel = root.find("channel")

        if channel is None:
            return

        observed_at = datetime.now(timezone.utc).isoformat()

        for item in channel.findall("item"):
            title = _text(item, "title")

            if not title:
                continue

            company = ""
            if ":" in title:
                company, title = (part.strip() for part in title.split(":", 1))

            link = _text(item, "link")
            description = _text(item, "description")
            region = _text(item, "region")
            country = _text(item, "country")
            state = _text(item, "state")
            employment_type = _text(item, "type")
            posted_at = _text(item, "pubDate")

            location_parts = [
                value
                for value in (region, state, country)
                if value
            ]

            yield Job(
                title=title,
                company=company,
                description=description,
                source=self.source_name,
                source_url=link,
                created_at=posted_at or observed_at,
                raw_data={
                    "region": region,
                    "country": country,
                    "state": state,
                    "employment_type": employment_type,
                },
            )
