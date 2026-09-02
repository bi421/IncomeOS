from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class JobApplication:
    job_id: int
    job_title: str
    job_url: str
    company: str
    applied_at: datetime
    status: str  # "PENDING", "SUBMITTED", "FAILED", "SKIPPED"
    cover_letter_path: Optional[str] = None
    error_message: Optional[str] = None
