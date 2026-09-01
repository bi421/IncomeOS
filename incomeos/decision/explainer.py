from __future__ import annotations
from .models import Decision

def explain_decision(decision: Decision) -> str:
    lines = [
        f"Decision for: {decision.opportunity_name}",
        f"  Score: {decision.opportunity_score:.3f}",
        f"  Readiness: {decision.readiness:.3f}",
        f"  Actionable: {decision.is_actionable}",
        f"  Severity: {decision.decision_severity.value}",
        f"  Action: {decision.action.command}",
        f"  Expected duration: {decision.action.expected_duration_minutes} min",
        "  Reasons:"
    ]
    for r in decision.reasons:
        lines.append(f"    - {r.text} (conf={r.confidence:.2f})")
    lines.append(f"  Explanation: {decision.explanation}")
    return "\n".join(lines)