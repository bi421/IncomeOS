from incomeos.insights.feedback import (
    identify_feedback_signals,
    summarize_outcomes,
)
from incomeos.tracking.outcomes import (
    OutcomeRecord,
    OutcomeType,
)


def outcome(
    outcome_type,
    evidence="email",
):
    return OutcomeRecord(
        outcome_id=None,
        decision_id="dec_1",
        job_id="job_1",
        outcome_type=outcome_type,
        evidence_source=evidence,
        evidence_text="observed",
        observed_at="2026-09-02T00:00:00+00:00",
        metadata={},
    )


def test_feedback_summary_counts_success_and_negative():
    summary = summarize_outcomes(
        (
            outcome(OutcomeType.INTERVIEW),
            outcome(OutcomeType.REJECTION),
            outcome(OutcomeType.OFFER),
        )
    )

    assert summary.total_outcomes == 3
    assert summary.successful_outcomes == 2
    assert summary.negative_outcomes == 1
    assert summary.externally_evidenced_outcomes == 3
    assert summary.success_rate == 2 / 3


def test_feedback_detects_positive_signal():
    signals = identify_feedback_signals(
        (
            outcome(OutcomeType.INTERVIEW),
            outcome(OutcomeType.OFFER),
        )
    )

    assert "resolved outcomes show positive signal" in signals
    assert "offer outcome detected" in signals


def test_feedback_detects_missing_evidence():
    signals = identify_feedback_signals(
        (
            outcome(
                OutcomeType.UNKNOWN,
                evidence="",
            ),
        )
    )

    assert (
        "outcomes exist without external evidence"
        in signals
    )


def test_empty_feedback_is_explicit():
    signals = identify_feedback_signals(())

    assert signals == (
        "no outcome evidence collected",
    )
