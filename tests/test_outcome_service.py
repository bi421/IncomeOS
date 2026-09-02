
import pytest

from incomeos.tracking.outcome_service import (
    ingest_external_outcome,
    ingest_local_application_state,
)
from incomeos.tracking.outcomes import (
    OutcomeStore,
    OutcomeType,
)


def test_external_outcome_is_persisted(tmp_path):
    store = OutcomeStore(
        tmp_path / "outcomes.db"
    )

    result = ingest_external_outcome(
        decision_id="dec_123",
        job_id="job_123",
        outcome_type=OutcomeType.INTERVIEW,
        evidence_source="email",
        evidence_text="Interview invitation received.",
        store=store,
    )

    assert result.outcome_id > 0
    assert result.evidence_source == "email"

    rows = store.list_for_decision(
        "dec_123"
    )

    assert len(rows) == 1
    assert rows[0].outcome_type is OutcomeType.INTERVIEW


def test_local_state_does_not_need_external_evidence(tmp_path):
    store = OutcomeStore(
        tmp_path / "outcomes.db"
    )

    result = ingest_local_application_state(
        decision_id="dec_456",
        job_id="job_456",
        state=OutcomeType.PREPARED,
        store=store,
    )

    assert result.outcome_id > 0
    assert result.evidence_source == ""

    rows = store.list_for_decision(
        "dec_456"
    )

    assert rows[0].outcome_type is OutcomeType.PREPARED


def test_invalid_external_outcome_without_evidence_fails(tmp_path):
    store = OutcomeStore(
        tmp_path / "outcomes.db"
    )

    with pytest.raises(ValueError):
        ingest_external_outcome(
            decision_id="dec_789",
            job_id="job_789",
            outcome_type=OutcomeType.OFFER,
            evidence_source="",
            evidence_text="offer",
            store=store,
        )
