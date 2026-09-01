from __future__ import annotations
from typing import Iterable
from incomeos.jobs.models.job import Job

class JobSourceAdapter:
    source_name: str = "unknown"

    def fetch(self) -> Iterable[Job]:
        raise NotImplementedError
