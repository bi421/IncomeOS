import re
from typing import Any

class JobResearcher:
    def __init__(self):
        pass

    def research(self, job: dict[str, Any]) -> dict[str, Any]:
        desc = job.get("desc", "") + " " + job.get("raw", "")
        text = desc.lower()

        # 1. Компанийн салбар
        industry = self._extract_industry(text)

        # 2. Компанийн хэмжээ (Startup / SME / Enterprise)
        size = self._extract_size(text)

        # 3. Санхүүжилт / Тогтвортой байдал (ойролцоогоор)
        funding = self._extract_funding(text)

        # 4. Зах зээлийн эрэлт (Энэ ур чадвар хэр их хэрэгтэй вэ?)
        demand = self._estimate_demand(job.get("title", ""))

        return {
            "industry": industry,
            "company_size": size,
            "funding_stage": funding,
            "market_demand": demand,
            "risk_level": "LOW" if funding in ["Series A", "Series B", "Public"] else "HIGH"
        }

    def _extract_industry(self, text: str) -> str:
        keywords = {
            "fintech": ["fintech", "financial", "banking", "payment", "crypto", "blockchain"],
            "adtech": ["adtech", "advertising", "marketing", "media", "reels", "content"],
            "healthtech": ["healthtech", "medical", "healthcare", "biotech"],
            "edtech": ["edtech", "education", "learning"],
            "ecommerce": ["ecommerce", "shop", "retail", "marketplace"],
            "ai": ["ai", "artificial intelligence", "llm", "machine learning"]
        }
        for industry, words in keywords.items():
            if any(w in text for w in words):
                return industry
        return "Unknown"

    def _extract_size(self, text: str) -> str:
        if any(w in text for w in ["10,000", "10000", "fortune 500", "enterprise"]):
            return "Enterprise"
        if any(w in text for w in ["500", "1000", "scale-up", "growth"]):
            return "SME"
        if any(w in text for w in ["startup", "early-stage", "seed", "angel"]):
            return "Startup"
        return "Unknown"

    def _extract_funding(self, text: str) -> str:
        if "series b" in text or "series c" in text:
            return "Series B+"
        if "series a" in text:
            return "Series A"
        if "seed" in text:
            return "Seed"
        if "ipo" in text or "public" in text:
            return "Public"
        return "Unknown"

    def _estimate_demand(self, title: str) -> str:
        high_demand = ["senior", "lead", "principal", "director", "head of"]
        medium_demand = ["engineer", "developer", "analyst", "specialist"]
        if any(w in title.lower() for w in high_demand):
            return "HIGH"
        if any(w in title.lower() for w in medium_demand):
            return "MEDIUM"
        return "LOW"
