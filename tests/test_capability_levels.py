from incomeos.skills.levels import (
    CapabilityLevel,
    capability_readiness_score,
    classify_capability_level,
)


def test_a_requires_multiple_repositories_and_evidence():
    level, reason = classify_capability_level(
        confidence=0.90,
        evidence_count=3,
        repository_count=2,
    )

    assert level is CapabilityLevel.A
    assert "multiple repositories" in reason


def test_high_confidence_alone_cannot_create_a():
    level, _ = classify_capability_level(
        confidence=1.00,
        evidence_count=1,
        repository_count=1,
    )

    assert level is CapabilityLevel.B


def test_b_represents_real_limited_evidence():
    level, _ = classify_capability_level(
        confidence=0.60,
        evidence_count=1,
        repository_count=1,
    )

    assert level is CapabilityLevel.B


def test_weak_evidence_is_unknown():
    level, _ = classify_capability_level(
        confidence=0.40,
        evidence_count=1,
        repository_count=1,
    )

    assert level is CapabilityLevel.UNKNOWN


def test_zero_evidence_is_unknown():
    level, _ = classify_capability_level(
        confidence=1.00,
        evidence_count=0,
        repository_count=0,
    )

    assert level is CapabilityLevel.UNKNOWN


def test_a_readiness_uses_confidence():
    assert capability_readiness_score(
        CapabilityLevel.A,
        0.91,
    ) == 0.91


def test_b_readiness_is_capped():
    assert capability_readiness_score(
        CapabilityLevel.B,
        0.95,
    ) == 0.70


def test_unknown_readiness_is_zero():
    assert capability_readiness_score(
        CapabilityLevel.UNKNOWN,
        1.0,
    ) == 0.0
