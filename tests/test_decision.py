from incomeos.decision.engine import (
    DecisionAction,
    DecisionInput,
    decide_application,
)


def test_low_match_is_rejected():
    assert decide_application(
        DecisionInput(0.69, True, True)
    ) is DecisionAction.REJECT


def test_failed_audit_is_rejected():
    assert decide_application(
        DecisionInput(0.90, False, True)
    ) is DecisionAction.REJECT


def test_unverified_skill_gap_requires_preparation():
    assert decide_application(
        DecisionInput(0.90, True, False)
    ) is DecisionAction.PREPARE_COVER_LETTER


def test_all_gates_pass_apply():
    assert decide_application(
        DecisionInput(0.90, True, True)
    ) is DecisionAction.APPLY


def test_threshold_is_configurable():
    assert decide_application(
        DecisionInput(0.65, True, True),
        threshold=0.60,
    ) is DecisionAction.APPLY


def test_invalid_score_fails_closed():
    import pytest

    with pytest.raises(ValueError):
        DecisionInput(1.1, True, True)
