from __future__ import annotations
from abc import ABC, abstractmethod
from typing import AsyncIterator, Any

class Source(ABC):
    name: str = "unknown"

    @abstractmethod
    async def fetch(self) -> AsyncIterator[dict[str, Any]]:
        pass

    @abstractmethod
    def validate(self, raw: dict[str, Any]) -> bool:
        pass
