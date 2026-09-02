from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


APPLICATION_PREPARED = "PREPARED"
APPLICATION_OPENED = "OPENED_IN_BROWSER"
APPLICATION_FAILED = "FAILED"
APPLICATION_SKIPPED = "SKIPPED"


@dataclass
class JobApplication:
    job_id: int
    job_title: str
    job_url: str
    company: str
    applied_at: datetime
    status: str
    cover_letter_path: Optional[str] = None
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        allowed = {
            APPLICATION_PREPARED,
            APPLICATION_OPENED,
            APPLICATION_FAILED,
            APPLICATION_SKIPPED,
        }

        if self.status not in allowed:
            raise ValueError(
                f"invalid application status: {self.status!r}"
            )
