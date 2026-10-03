from incomeos.decision.engine import DecisionAction, make_decision
from incomeos.opportunities.engine import IncomeOpportunity, OpportunityMatch


def _patch_match(monkeypatch, match):
    monkeypatch.setattr(
        "incomeos.decision.engine.build_master_profile",
        lambda root: object(),
    )
    monkeypatch.setattr(
        "incomeos.decision.engine.match_opportunities",
        lambda profile: (match,),
    )


def _match():
    opportunity = IncomeOpportunity(
        name="Test",
        description="Test opportunity",
        required_skills=("Python",),
        skill_weights=(1.0,),
        base_value=1.0,
        difficulty=0.0,
    )
    return OpportunityMatch(
        opportunity=opportunity,
        readiness=1.0,
        opportunity_score=1.0,
        matched_skills=("Python",),
        missing_skills=(),
    )


def test_make_decision_fails_closed_without_explicit_audit(monkeypatch, tmp_path):
    _patch_match(monkeypatch, _match())
    decision = make_decision(tmp_path, audit_pass=False)
    assert decision is not None
    assert decision.action.command == DecisionAction.REJECT.value
    assert decision.is_actionable is False


def test_make_decision_allows_explicit_audit(monkeypatch, tmp_path):
    _patch_match(monkeypatch, _match())
    decision = make_decision(tmp_path, audit_pass=True)
    assert decision is not None
    assert decision.action.command == DecisionAction.APPLY.value
    assert decision.is_actionable is True
