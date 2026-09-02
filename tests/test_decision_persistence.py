from pathlib import Path

from incomeos.decision.persistence import (
    DecisionStore,
    create_decision,
    stable_decision_id,
)


def evidence():
    return (
        {
            "skill": "Python",
            "source": "bi421/ResearchOS",
            "evidence_type": "repository",
            "confidence": 0.95,
        },
    )


def test_stable_decision_id_is_deterministic():
    kwargs = {
        "job_id": "job-42",
        "opportunity_name": "Python Automation",
        "decision": "APPLY",
        "score": 0.81,
        "reason": "verified capability match",
        "evidence_snapshot": evidence(),
    }

    first = stable_decision_id(**kwargs)
    second = stable_decision_id(**kwargs)

    assert first == second
    assert first.startswith("dec_")


def test_decision_id_changes_when_evidence_changes():
    base = {
        "job_id": "job-42",
        "opportunity_name": "Python Automation",
        "decision": "APPLY",
        "score": 0.81,
        "reason": "verified capability match",
        "evidence_snapshot": evidence(),
    }

    changed = dict(base)
    changed["score"] = 0.82

    assert stable_decision_id(**base) != stable_decision_id(
        **changed
    )


def test_decision_round_trip(tmp_path: Path):
    db = tmp_path / "decisions.db"
    store = DecisionStore(db)

    record = create_decision(
        job_id="job-42",
        opportunity_name="Python Automation",
        decision="APPLY",
        score=0.81,
        reason="verified capability match",
        evidence_snapshot=evidence(),
    )

    store.save(record)

    loaded = store.get(record.decision_id)

    assert loaded is not None
    assert loaded.decision_id == record.decision_id
    assert loaded.job_id == "job-42"
    assert loaded.opportunity_name == "Python Automation"
    assert loaded.decision == "APPLY"
    assert loaded.score == 0.81
    assert loaded.reason == "verified capability match"
    assert loaded.evidence_snapshot == evidence()


def test_same_decision_can_be_saved_idempotently(tmp_path: Path):
    db = tmp_path / "decisions.db"
    store = DecisionStore(db)

    record = create_decision(
        job_id="job-99",
        opportunity_name="Data Engineering Support",
        decision="REVIEW",
        score=0.66,
        reason="partial evidence",
        evidence_snapshot=evidence(),
    )

    store.save(record)
    store.save(record)

    loaded = store.get(record.decision_id)

    assert loaded == record
