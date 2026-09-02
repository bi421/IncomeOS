
from incomeos.insights.feedback_store import (
    FeedbackStore,
    build_feedback,
)
from incomeos.tracking.outcomes import (
    OutcomeRecord,
    OutcomeType,
)


def outcome(
    outcome_type,
    evidence_source="email",
):
    return OutcomeRecord(
        outcome_id=None,
        decision_id="dec_123",
        job_id="job_123",
        outcome_type=outcome_type,
        evidence_source=evidence_source,
        evidence_text="Verified external evidence.",
        observed_at="2026-09-02T00:00:00+00:00",
        metadata={},
    )


def test_offer_creates_one_proposal_for_one_outcome(tmp_path):
    store = FeedbackStore(
        tmp_path / "feedback.db"
    )

    feedback = build_feedback(
        decision_id="dec_123",
        job_id="job_123",
        outcomes=(
            outcome(OutcomeType.OFFER),
        ),
        skills=("Python",),
        store=store,
    )

    assert feedback.feedback_id is not None
    assert len(feedback.proposal_ids) == 1

    proposals = store.list_proposals(
        "dec_123"
    )

    assert len(proposals) == 1
    assert proposals[0].skill == "Python"
    assert proposals[0].basis_outcome is OutcomeType.OFFER
    assert (
        proposals[0].status
        == "PENDING_HUMAN_VERIFICATION"
    )


def test_two_positive_outcomes_create_two_proposals(tmp_path):
    store = FeedbackStore(
        tmp_path / "feedback.db"
    )

    feedback = build_feedback(
        decision_id="dec_456",
        job_id="job_456",
        outcomes=(
            outcome(OutcomeType.INTERVIEW),
            outcome(OutcomeType.OFFER),
        ),
        skills=("Python", "Testing"),
        store=store,
    )

    assert len(feedback.proposal_ids) == 2

    proposals = store.list_proposals(
        "dec_456"
    )

    assert len(proposals) == 2
    assert all(
        item.skill
        == "REQUIRES_HUMAN_SKILL_ATTRIBUTION"
        for item in proposals
    )


def test_rejection_does_not_create_positive_skill_proposal(tmp_path):
    store = FeedbackStore(
        tmp_path / "feedback.db"
    )

    feedback = build_feedback(
        decision_id="dec_789",
        job_id="job_789",
        outcomes=(
            outcome(OutcomeType.REJECTION),
        ),
        skills=("Python",),
        store=store,
    )

    assert feedback.proposal_ids == ()


def test_feedback_persists_signals(tmp_path):
    store = FeedbackStore(
        tmp_path / "feedback.db"
    )

    feedback = build_feedback(
        decision_id="dec_900",
        job_id="job_900",
        outcomes=(
            outcome(OutcomeType.INTERVIEW),
            outcome(OutcomeType.OFFER),
        ),
        skills=("Python", "Testing"),
        store=store,
    )

    assert (
        "offer outcome detected"
        in feedback.signals
    )

    assert len(
        feedback.proposal_ids
    ) == 2

    assert feedback.feedback_id is not None
