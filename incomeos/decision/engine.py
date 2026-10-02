from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from incomeos.applications.generator import EvidenceBoundGenerator
from incomeos.decision.models import (
    ActionPlan,
    Decision,
    DecisionReason,
    DecisionSeverity,
)
from incomeos.opportunities.engine import OpportunityMatch, match_opportunities
from incomeos.skills.aggregator import build_master_profile


class DecisionAction(str, Enum):
    """Deterministic next actions for a concrete job opportunity."""

    APPLY = "APPLY"
    PREPARE_COVER_LETTER = "PREPARE_COVER_LETTER"
    REJECT = "REJECT"


@dataclass(frozen=True)
class DecisionInput:
    """Evidence required to make an application decision."""

    match_score: float
    audit_pass: bool
    skill_gap_verified: bool
    opportunity_name: str = "unknown"
    job_id: str = ""
    job_description: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.match_score <= 1.0:
            raise ValueError("match_score must be between 0 and 1")


MATCH_THRESHOLD = 0.70


def decide_application(
    decision: DecisionInput,
    *,
    threshold: float = MATCH_THRESHOLD,
) -> DecisionAction:
    """Apply deterministic gates in fixed order and fail closed."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")

    if decision.match_score < threshold:
        return DecisionAction.REJECT
    if not decision.audit_pass:
        return DecisionAction.REJECT
    if not decision.skill_gap_verified:
        return DecisionAction.PREPARE_COVER_LETTER
    return DecisionAction.APPLY


def _decision_from_match(
    match: OpportunityMatch,
    *,
    audit_pass: bool,
    skill_gap_verified: bool,
) -> Decision:
    action = decide_application(
        DecisionInput(
            match_score=match.opportunity_score,
            audit_pass=audit_pass,
            skill_gap_verified=skill_gap_verified,
            opportunity_name=match.opportunity.name,
        )
    )
    reasons = (
        DecisionReason(
            f"match_score={match.opportunity_score:.3f}",
            confidence=match.opportunity_score,
        ),
        DecisionReason(
            f"audit_pass={audit_pass}",
            confidence=1.0 if audit_pass else 0.0,
        ),
        DecisionReason(
            f"skill_gap_verified={skill_gap_verified}",
            confidence=1.0 if skill_gap_verified else 0.0,
        ),
        DecisionReason(
            f"matched_skills={','.join(match.matched_skills) or 'none'}",
            confidence=1.0,
        ),
        DecisionReason(
            f"missing_skills={','.join(match.missing_skills) or 'none'}",
            confidence=0.0 if match.missing_skills else 1.0,
        ),
    )
    severity = (
        DecisionSeverity.HIGH
        if action is DecisionAction.APPLY
        else DecisionSeverity.MEDIUM
    )
    plan = ActionPlan(
        opportunity_name=match.opportunity.name,
        command=action.value,
        expected_duration_minutes=5,
        risk_level=severity,
    )
    return Decision(
        opportunity_name=match.opportunity.name,
        opportunity_score=match.opportunity_score,
        readiness=match.readiness,
        reasons=reasons,
        action=plan,
        decision_severity=severity,
        is_actionable=action is not DecisionAction.REJECT,
        explanation=f"Deterministic decision: {action.value}",
    )


def make_decision(
    repos_root: str | Path,
    force: bool = False,
    data_dir: Path = Path("data"),
) -> Decision | None:
    """Evaluate the best evidence-backed opportunity without executing it."""
    del force, data_dir
    profile = build_master_profile(Path(repos_root))
    matches = match_opportunities(profile)
    if not matches:
        return None
    top = matches[0]
    audit_pass = True
    skill_gap_verified = not bool(top.missing_skills)
    return _decision_from_match(
        top,
        audit_pass=audit_pass,
        skill_gap_verified=skill_gap_verified,
    )


class DecisionEngine:
    """Compatibility facade for the deterministic decision engine."""

    @staticmethod
    def decide(
        repos_root: str | Path,
        force: bool = False,
    ) -> Decision | None:
        return make_decision(repos_root, force)


def prepare_cover_letter(
    *,
    profile_path: str | Path,
    job_description: str,
) -> str:
    """Prepare evidence-bound cover-letter material; never submit it."""
    return EvidenceBoundGenerator(profile_path).generate(job_description).cover_letter
