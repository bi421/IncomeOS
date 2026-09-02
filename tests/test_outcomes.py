import pytest

from incomeos.tracking.outcomes import (
    OutcomeStore,
    OutcomeType,
    create_outcome,
)


def test_external_submission_requires_evidence():
    with pytest.raises(ValueError):
        create_outcome(
            decision_id="dec_123",
            job_id="job-1",
            outcome_type=OutcomeType.SUBMITTED,
        )


def test_external_outcome_round_trip(tmp_path):
    store = OutcomeStore(
        tmp_path / "outcomes.db"
    )

    record = create_outcome(
        decision_id="dec_123",
        job_id="job-1",
        outcome_type=OutcomeType.INTERVIEW,
        evidence_source="email",
        evidence_text="Interview invitation received",
        metadata={"round": 1},
    )

    outcome_id = store.save(record)

    assert outcome_id > 0

    loaded = store.list_for_decision(
        "dec_123"
    )

    assert len(loaded) == 1
    assert loaded[0].job_id == "job-1"
    assert loaded[0].outcome_type is OutcomeType.INTERVIEW
    assert loaded[0].evidence_source == "email"
    assert loaded[0].metadata == {"round": 1}


def test_local_preparation_can_exist_without_external_evidence():
    record = create_outcome(
        decision_id="dec_123",
        job_id="job-1",
        outcome_type=OutcomeType.PREPARED,
    )

    assert record.evidence_source == ""
