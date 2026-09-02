from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Any

class Normalizer:
    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": raw.get("source", "unknown"),
            "title": self._clean_title(raw.get("title", "")),
            "company": self._extract_company(raw),
            "url": raw.get("url", ""),
            "salary": self._normalize_salary(raw),
            "location": self._normalize_location(raw),
            "description": raw.get("description", ""),
            "created_at": self._normalize_created_at(raw.get("created_at")),
            "raw_data": raw,
        }

    def _clean_title(self, title: str) -> str:
        return re.sub(r"\s+", " ", title.strip())

    def _extract_company(self, raw: dict) -> str:
        for key in ["company_name", "company", "employer", "Organization"]:
            if key in raw and raw[key]:
                return raw[key]
        return "Unknown"

    def _normalize_salary(self, raw: dict) -> dict | None:
        salary_text = raw.get("salary", "")
        if not salary_text:
            return None
        numbers = re.findall(r"[\d,]+", salary_text)
        if len(numbers) >= 2:
            return {
                "min": self._parse_number(numbers[0]),
                "max": self._parse_number(numbers[1]),
                "currency": "USD" if "$" in salary_text else "EUR"
            }
        return None

    def _normalize_location(self, raw: dict) -> dict:
        loc = raw.get("location", "") or raw.get("city", "") or raw.get("country", "")
        return {
            "text": loc,
            "country": raw.get("country", ""),
            "remote": raw.get("remote", False),
        }

    def _normalize_created_at(self, value: Any) -> str:
        if value is None:
            return datetime.now(timezone.utc).isoformat()
        if isinstance(value, int):
            return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
        if isinstance(value, str):
            try:
                # ISO формат эсэхийг шалгах
                datetime.fromisoformat(value)
                return value
            except:
                return datetime.now(timezone.utc).isoformat()
        return datetime.now(timezone.utc).isoformat()

    def _parse_number(self, s: str) -> float:
        return float(re.sub(r"[^\d.]", "", s))
