from __future__ import annotations
import aiohttp
from typing import AsyncIterator, Any
from .base import Source

class ArbeitnowSource(Source):
    name = "arbeitnow"

    async def fetch(self) -> AsyncIterator[dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.arbeitnow.com/api/job-board-api") as resp:
                data = await resp.json()
                for item in data.get("data", []):
                    yield item

    def validate(self, raw: dict[str, Any]) -> bool:
        return bool(raw.get("title") and raw.get("url"))
