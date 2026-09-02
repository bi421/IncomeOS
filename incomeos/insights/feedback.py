from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
from typing import Iterable

from incomeos.tracking.outcomes import (
    OutcomeRecord,
    OutcomeType,
)


@dataclass(frozen=True)
class FeedbackSummary:
    total_outcomes: int
    successful_outcomes: int
    negative_outcomes: int
    externally_evidenced_outcomes: int
    outcome_counts: dict[str, int]
    success_rate: float | None


SUCCESS_TYPES = {
    OutcomeType.INTERVIEW,
    OutcomeType.OFFER,
}

NEGATIVE_TYPES = {
    OutcomeType.REJECTION,
    OutcomeType.WITHDRAWN,
}


def summarize_outcomes(
    outcomes: Iterable[OutcomeRecord],
) -> FeedbackSummary:
    items = tuple(outcomes)

    counts = Counter(
        item.outcome_type.value
        for item in items
    )

    successful = sum(
        1
        for item in items
        if item.outcome_type in SUCCESS_TYPES
    )

    negative = sum(
        1
        for item in items
        if item.outcome_type in NEGATIVE_TYPES
    )

    externally_evidenced = sum(
        1
        for item in items
        if item.evidence_source.strip()
    )

    resolved = successful + negative

    success_rate = (
        successful / resolved
        if resolved > 0
        else None
    )

    return FeedbackSummary(
        total_outcomes=len(items),
        successful_outcomes=successful,
        negative_outcomes=negative,
        externally_evidenced_outcomes=externally_evidenced,
        outcome_counts=dict(counts),
        success_rate=success_rate,
    )


def identify_feedback_signals(
    outcomes: Iterable[OutcomeRecord],
) -> tuple[str, ...]:
    summary = summarize_outcomes(outcomes)

    signals: list[str] = []

    if summary.total_outcomes == 0:
        signals.append(
            "no outcome evidence collected"
        )
        return tuple(signals)

    if summary.externally_evidenced_outcomes == 0:
        signals.append(
            "outcomes exist without external evidence"
        )

    if summary.success_rate is not None:
        if summary.success_rate == 0.0:
            signals.append(
                "all resolved outcomes are negative"
            )
        elif summary.success_rate >= 0.5:
            signals.append(
                "resolved outcomes show positive signal"
            )

    if summary.outcome_counts.get(
        OutcomeType.REJECTION.value,
        0,
    ) >= 3:
        signals.append(
            "rejection pattern detected"
        )

    if summary.outcome_counts.get(
        OutcomeType.INTERVIEW.value,
        0,
    ) >= 2:
        signals.append(
            "interview conversion signal detected"
        )

    if summary.outcome_counts.get(
        OutcomeType.OFFER.value,
        0,
    ) >= 1:
        signals.append(
            "offer outcome detected"
        )

    return tuple(signals)
