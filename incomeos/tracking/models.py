from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ExecutionLog:
    id: Optional[int]
    opportunity_name: str
    action_command: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    exit_code: Optional[int]
    output_log: str
    error_log: str
