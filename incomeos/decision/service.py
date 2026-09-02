from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from incomeos.decision.persistence import (
    DecisionRecord,
    DecisionStore,
    create_decision,
)
from incomeos.jobs.fit import JobFit


@dataclass(frozen=True)
class DecisionEvaluation:
    record: DecisionRecord
    persisted: bool


def _evidence_from_fit(
    fit: JobFit,
) -> tuple[dict[str, Any], ...]:
    return (
        {
            "job_id": fit.job_id,
            "fit_score": fit.fit_score,
            "matched_requirements": list(
                fit.matched_requirements
            ),
            "missing_requirements": list(
                fit.missing_requirements
            ),
            "reasons": list(fit.reasons),
        },
    )


def decision_from_job_fit(
    *,
    fit: JobFit,
    opportunity_name: str,
    decision: str,
    store: DecisionStore,
) -> DecisionEvaluation:
    """
    Canonical bridge between Job Fit and persistent Decision.

    The decision is derived from the supplied JobFit and stores the
    exact fit explanation used to reach it.
    """

    reason = (
        "; ".join(fit.reasons)
        if fit.reasons
        else "no additional fit reasons"
    )

    evidence_snapshot = _evidence_from_fit(fit)

    record = create_decision(
        job_id=fit.job_id,
        opportunity_name=opportunity_name,
        decision=decision,
        score=fit.fit_score,
        reason=reason,
        evidence_snapshot=evidence_snapshot,
    )

    store.save(record)

    return DecisionEvaluation(
        record=record,
        persisted=True,
    )


def evaluate_and_persist(
    *,
    fit: JobFit,
    opportunity_name: str,
    apply_threshold: float = 1.0,
    store: DecisionStore | None = None,
) -> DecisionEvaluation:
    """
    Turn an already-evaluated JobFit into an explicit persisted decision.

    APPLY is only selected when the required-fit threshold is met.
    Otherwise REVIEW is persisted.

    No external submission is implied.
    """

    if not 0.0 <= apply_threshold <= 1.0:
        raise ValueError(
            "apply_threshold must be between 0 and 1"
        )

    if store is None:
        store = DecisionStore()

    decision = (
        "APPLY"
        if fit.fit_score >= apply_threshold
        and not fit.missing_requirements
        else "REVIEW"
    )

    return decision_from_job_fit(
        fit=fit,
        opportunity_name=opportunity_name,
        decision=decision,
        store=store,
    )


def load_decision(
    decision_id: str,
    store: DecisionStore | None = None,
) -> DecisionRecord | None:
    if store is None:
        store = DecisionStore()

    return store.get(decision_id)
