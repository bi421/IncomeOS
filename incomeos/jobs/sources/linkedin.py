from __future__ import annotations
import json
import re
import urllib.request
from datetime import datetime, timezone
from typing import Iterable

from incomeos.jobs.models.job import Job
from .base import JobSourceAdapter

class LinkedInSource(JobSourceAdapter):
    source_name = "linkedin"

    def fetch(self) -> Iterable[Job]:
        """
        LinkedIn дээр Python хайлтаар ажлын байр хайх.
        Анхааруулга: LinkedIn бодит API өгөхгүй тул HTML parse хийх.
        Хэрэв бүтэлгүйтвэл хоосон буцаана.
        """
        skill = "python"
        url = f"https://www.linkedin.com/jobs/search/?keywords={skill}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8")
        except Exception as e:
            print(f"⚠️ LinkedIn fetch failed: {e}")
            return

        # Жишээ regex (бодит байдал дээр Selenium эсвэл API хэрэгтэй)
        job_pattern = r'"jobTitle":"([^"]+)"[^}]+"companyName":"([^"]+)"[^}]+"jobPostingUrl":"([^"]+)"'
        matches = re.findall(job_pattern, html)

        observed_at = datetime.now(timezone.utc).isoformat()
        for title, company, url_path in matches[:20]:  # 20 ажлын байр
            full_url = "https://www.linkedin.com" + url_path.replace("\\u002F", "/")
            yield Job(
                source=self.source_name,
                title=title,
                source_url=full_url,
                company=company,
                description="LinkedIn job",
                created_at=observed_at,
                raw_data={"title": title, "company": company, "url": full_url},
            )
