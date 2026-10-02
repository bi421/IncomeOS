from incomeos.tracking.models import ActionState
from incomeos.tracking.tracker import ApplicationStatus, ApplicationTracker


def test_tracker_lifecycle(tmp_path):
    tracker = ApplicationTracker(tmp_path / "tracking.db")
    record = tracker.scout("42", "Python Engineer", "Example Co")
    assert record.status is ApplicationStatus.SCOUTED

    applied = tracker.transition("42", ApplicationStatus.APPLIED, "user-confirmed")
    assert applied.status is ApplicationStatus.APPLIED

    interviewing = tracker.transition("42", ApplicationStatus.INTERVIEWING, "email evidence")
    assert interviewing.status is ApplicationStatus.INTERVIEWING

    offer = tracker.transition("42", ApplicationStatus.OFFER, "offer email")
    assert offer.status is ApplicationStatus.OFFER


def test_tracker_rejects_invalid_transition(tmp_path):
    tracker = ApplicationTracker(tmp_path / "tracking.db")
    tracker.scout("42", "Python Engineer", "Example Co")
    try:
        tracker.transition("42", ApplicationStatus.OFFER)
    except ValueError as exc:
        assert "invalid transition" in str(exc)
    else:
        raise AssertionError("invalid transition was accepted")


def test_tracker_unknown_job_fails_closed(tmp_path):
    tracker = ApplicationTracker(tmp_path / "tracking.db")
    try:
        tracker.transition("missing", ApplicationStatus.APPLIED)
    except KeyError:
        pass
    else:
        raise AssertionError("unknown job was accepted")


def test_existing_action_contract_remains_separate():
    assert ActionState.SUBMITTED.value == "submitted"
