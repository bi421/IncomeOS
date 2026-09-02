
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from incomeos.tracking.outcomes import (
    OutcomeStore,
    OutcomeType,
    create_outcome,
)


@dataclass(frozen=True)
class OutcomeIngestionResult:
    outcome_id: int
    decision_id: str
    job_id: str
    outcome_type: OutcomeType
    evidence_source: str


def ingest_external_outcome(
    *,
    decision_id: str,
    job_id: str,
    outcome_type: OutcomeType,
    evidence_source: str,
    evidence_text: str,
    metadata: dict[str, Any] | None = None,
    store: OutcomeStore | None = None,
) -> OutcomeIngestionResult:
    if not evidence_source.strip():
        raise ValueError(
            "external outcome requires evidence_source"
        )

    if not evidence_text.strip():
        raise ValueError(
            "external outcome requires evidence_text"
        )

    if store is None:
        store = OutcomeStore()

    record = create_outcome(
        decision_id=decision_id,
        job_id=job_id,
        outcome_type=outcome_type,
        evidence_source=evidence_source,
        evidence_text=evidence_text,
        metadata=metadata,
    )

    outcome_id = store.save(record)

    return OutcomeIngestionResult(
        outcome_id=outcome_id,
        decision_id=decision_id,
        job_id=job_id,
        outcome_type=outcome_type,
        evidence_source=evidence_source,
    )


def ingest_local_application_state(
    *,
    decision_id: str,
    job_id: str,
    state: OutcomeType,
    store: OutcomeStore | None = None,
) -> OutcomeIngestionResult:
    if state not in {
        OutcomeType.PREPARED,
        OutcomeType.OPENED_IN_BROWSER,
    }:
        raise ValueError(
            "local state must be PREPARED or OPENED_IN_BROWSER"
        )

    if store is None:
        store = OutcomeStore()

    record = create_outcome(
        decision_id=decision_id,
        job_id=job_id,
        outcome_type=state,
    )

    outcome_id = store.save(record)

    return OutcomeIngestionResult(
        outcome_id=outcome_id,
        decision_id=decision_id,
        job_id=job_id,
        outcome_type=state,
        evidence_source="",
    )
