from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class DecisionSeverity(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass(frozen=True)
class DecisionReason:
    text: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 1.0

@dataclass(frozen=True)
class ActionPlan:
    opportunity_name: str
    command: str
    expected_duration_minutes: int = 5
    risk_level: DecisionSeverity = DecisionSeverity.MEDIUM

@dataclass(frozen=True)
class Decision:
    opportunity_name: str
    opportunity_score: float
    readiness: float
    reasons: tuple[DecisionReason, ...]
    action: ActionPlan
    decision_severity: DecisionSeverity
    is_actionable: bool
    explanation: str