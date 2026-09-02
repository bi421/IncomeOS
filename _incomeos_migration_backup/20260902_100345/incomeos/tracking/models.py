from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ActionState(Enum):
    """The observed state of an action, not an inferred business outcome."""

    PLANNED = "planned"
    PREPARED = "prepared"
    DISABLED = "disabled"
    EXECUTED = "executed"
    FAILED = "failed"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"


@dataclass(frozen=True)
class ActionResult:
    """A truthful record of local execution and any external outcome.

    ``EXECUTED`` only means that a local command completed successfully. It
    never implies that an external application was submitted or confirmed.
    """

    action_name: str
    requested_command: str
    state: ActionState
    executed_command: tuple[str, ...] = ()
    exit_code: Optional[int] = None
    output_log: str = ""
    error_log: str = ""
    externally_submitted: bool = False
    externally_confirmed: bool = False

    def __post_init__(self) -> None:
        if self.externally_confirmed and not self.externally_submitted:
            raise ValueError("confirmation requires an external submission")
        if self.state is ActionState.SUBMITTED and not self.externally_submitted:
            raise ValueError("SUBMITTED requires an external submission")
        if self.state is ActionState.CONFIRMED and not self.externally_confirmed:
            raise ValueError("CONFIRMED requires external confirmation")

@dataclass
class ExecutionLog:
    id: Optional[int]
    opportunity_name: str
    action_command: str
    state: ActionState
    started_at: datetime
    finished_at: Optional[datetime]
    exit_code: Optional[int]
    output_log: str
    error_log: str
    executed_command: str = ""
    externally_submitted: bool = False
    externally_confirmed: bool = False

    @property
    def status(self) -> str:
        """Compatibility view for callers that previously read ``status``."""
        return self.state.value
