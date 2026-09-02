
import pytest

from incomeos.skills.verification import (
    VerificationStatus,
    VerificationStore,
)


def test_verified_proposal_is_persisted(tmp_path):
    store = VerificationStore(
        tmp_path / "verification.db"
    )

    record = store.verify(
        proposal_id=1,
        decision_id="dec_1",
        job_id="job_1",
        skill="Python",
        evidence_source="email",
        evidence_text="Offer received.",
        verifier_note="Confirmed by human.",
    )

    assert record.status is VerificationStatus.VERIFIED

    rows = store.list_verified()

    assert len(rows) == 1
    assert rows[0].skill == "Python"
    assert rows[0].decision_id == "dec_1"


def test_verified_proposal_cannot_be_verified_twice(tmp_path):
    store = VerificationStore(
        tmp_path / "verification.db"
    )

    store.verify(
        proposal_id=1,
        decision_id="dec_1",
        job_id="job_1",
        skill="Python",
        evidence_source="email",
        evidence_text="Offer received.",
    )

    with pytest.raises(ValueError):
        store.verify(
            proposal_id=1,
            decision_id="dec_1",
            job_id="job_1",
            skill="Python",
            evidence_source="email",
            evidence_text="Offer received again.",
        )


def test_verification_requires_external_evidence(tmp_path):
    store = VerificationStore(
        tmp_path / "verification.db"
    )

    with pytest.raises(ValueError):
        store.verify(
            proposal_id=2,
            decision_id="dec_2",
            job_id="job_2",
            skill="Python",
            evidence_source="",
            evidence_text="",
        )


def test_rejected_proposal_is_not_verified(tmp_path):
    store = VerificationStore(
        tmp_path / "verification.db"
    )

    record = store.reject(
        proposal_id=3,
        decision_id="dec_3",
        job_id="job_3",
        skill="Python",
        reason="Evidence does not establish skill attribution.",
    )

    assert record.status is VerificationStatus.REJECTED
    assert store.list_verified() == ()
