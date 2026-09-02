from __future__ import annotations

from enum import StrEnum


class CapabilityLevel(StrEnum):
    """
    Evidence-backed capability breadth.

    Confidence and professional capability level are intentionally separate.

    A:
        Strong repeated evidence across multiple repositories.

    B:
        Real evidence exists, but breadth/repetition is insufficient for A.

    UNKNOWN:
        Evidence is insufficient for a defensible capability level.
    """

    A = "A"
    B = "B"
    UNKNOWN = "UNKNOWN"


def classify_capability_level(
    *,
    confidence: float,
    evidence_count: int,
    repository_count: int,
) -> tuple[CapabilityLevel, str]:
    """
    Classify capability level from evidence breadth.

    A:
        confidence >= 0.80
        evidence >= 2
        repositories >= 2

    B:
        confidence >= 0.50
        evidence >= 1
        repositories >= 1

    UNKNOWN:
        anything weaker.

    Confidence alone can never create A.
    """

    if (
        confidence >= 0.80
        and evidence_count >= 2
        and repository_count >= 2
    ):
        return (
            CapabilityLevel.A,
            "strong confidence with repeated evidence across multiple repositories",
        )

    if (
        confidence >= 0.50
        and evidence_count >= 1
        and repository_count >= 1
    ):
        return (
            CapabilityLevel.B,
            "real evidence exists but breadth is insufficient for A",
        )

    return (
        CapabilityLevel.UNKNOWN,
        "insufficient evidence for a defensible capability level",
    )


def capability_readiness_score(
    level: CapabilityLevel,
    confidence: float,
) -> float:
    """
    Convert an evidence-backed capability level into an opportunity
    readiness score.

    A keeps the full evidence confidence.

    B is intentionally capped at 0.70 so that limited evidence cannot
    look equivalent to a broad capability.

    UNKNOWN contributes zero readiness.
    """

    confidence = max(0.0, min(1.0, float(confidence)))

    if level is CapabilityLevel.A:
        return confidence

    if level is CapabilityLevel.B:
        return min(confidence, 0.70)

    return 0.0
