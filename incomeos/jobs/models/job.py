from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Job:
    source: str
    title: str
    source_url: str          # тестэд хэрэглэгддэг
    company: str = ""
    description: str = ""
    created_at: str = ""     # default хоосон
    raw_data: dict[str, Any] = field(default_factory=dict)
    url: str = ""            # source_url-тай ижил утгатай байх болно

    def __post_init__(self):
        if not self.url and self.source_url:
            self.url = self.source_url
        if not self.source_url and self.url:
            self.source_url = self.url

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "source_url": self.source_url,
            "company": self.company,
            "description": self.description,
            "created_at": self.created_at,
            "raw_data": str(self.raw_data),
        }
