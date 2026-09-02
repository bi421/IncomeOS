from __future__ import annotations

from incomeos.executor import orchestrator
from incomeos.opportunities.engine import (
    IncomeOpportunity,
    OpportunityMatch,
)
from incomeos.decision.persistence import DecisionStore


def test_live_opportunity_persists_decision(
    monkeypatch,
    tmp_path,
):
    opportunity = IncomeOpportunity(
        name="Python Automation",
        description="Test opportunity.",
        required_skills=("Python",),
        skill_weights=(1.0,),
        base_value=0.9,
        difficulty=0.2,
    )

    match = OpportunityMatch(
        opportunity=opportunity,
        readiness=1.0,
        opportunity_score=0.8,
        matched_skills=("Python",),
        missing_skills=(),
        readiness_basis="skill_confidence",
    )

    monkeypatch.setattr(
        orchestrator,
        "build_master_profile",
        lambda _: object(),
    )

    monkeypatch.setattr(
        orchestrator,
        "match_opportunities",
        lambda _: (match,),
    )

    monkeypatch.setattr(
        orchestrator,
        "log_start",
        lambda *_: 1,
    )

    monkeypatch.setattr(
        orchestrator,
        "log_finish",
        lambda *_: None,
    )

    db = tmp_path / "decisions.db"

    result = orchestrator.run_opportunity(
        tmp_path,
        force=True,
        decision_db_path=db,
    )

    assert result is not None

    store = DecisionStore(db)

    rows = list(
        store._connect().execute(
            """
            SELECT
                decision_id,
                job_id,
                opportunity_name,
                decision,
                score,
                evidence_snapshot
            FROM decisions
            """
        ).fetchall()
    )

    assert len(rows) == 1
    assert rows[0][1] == "opportunity:Python Automation"
    assert rows[0][2] == "Python Automation"
    assert rows[0][3] == "APPLY"
    assert rows[0][4] == 1.0
    assert "matched" in rows[0][5]


def test_runtime_decision_does_not_claim_submission(
    monkeypatch,
    tmp_path,
):
    opportunity = IncomeOpportunity(
        name="Python Automation",
        description="Test opportunity.",
        required_skills=("Python",),
        skill_weights=(1.0,),
        base_value=0.9,
        difficulty=0.2,
    )

    match = OpportunityMatch(
        opportunity=opportunity,
        readiness=0.5,
        opportunity_score=0.4,
        matched_skills=("Python",),
        missing_skills=(),
        readiness_basis="capability_level_and_evidence_confidence",
    )

    monkeypatch.setattr(
        orchestrator,
        "build_master_profile",
        lambda _: object(),
    )

    monkeypatch.setattr(
        orchestrator,
        "match_opportunities",
        lambda _: (match,),
    )

    monkeypatch.setattr(
        orchestrator,
        "log_start",
        lambda *_: 1,
    )

    monkeypatch.setattr(
        orchestrator,
        "log_finish",
        lambda *_: None,
    )

    db = tmp_path / "decisions.db"

    result = orchestrator.run_opportunity(
        tmp_path,
        force=True,
        decision_db_path=db,
    )

    assert result is not None
    assert not result.externally_submitted
    assert not result.externally_confirmed

    store = DecisionStore(db)

    record = store.get(
        next(
            row[0]
            for row in store._connect().execute(
                "SELECT decision_id FROM decisions"
            ).fetchall()
        )
    )

    assert record is not None
    assert record.decision == "REVIEW"
