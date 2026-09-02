from __future__ import annotations
import asyncio
from typing import Any
from .sources import ArbeitnowSource
from .normalizer import Normalizer

class IngestPipeline:
    def __init__(self):
        self.sources = [ArbeitnowSource()]
        self.normalizer = Normalizer()

    async def run(self, limit: int = 10) -> list[dict[str, Any]]:
        results = []
        for source in self.sources:
            async for raw in source.fetch():
                if not source.validate(raw):
                    continue
                normalized = self.normalizer.normalize({
                    **raw,
                    "source": source.name
                })
                results.append(normalized)
                if len(results) >= limit:
                    return results
        return results
