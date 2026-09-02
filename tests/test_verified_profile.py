
from incomeos.skills.verification import (
    VerificationRecord,
    VerificationStatus,
)
from incomeos.skills.verified_profile import (
    build_verified_profile_projection,
)


def verified(
    proposal_id,
    skill,
    decision_id,
    job_id,
    source,
):
    return VerificationRecord(
        verification_id=proposal_id,
        proposal_id=proposal_id,
        decision_id=decision_id,
        job_id=job_id,
        skill=skill,
        status=VerificationStatus.VERIFIED,
        verifier_note="confirmed",
        evidence_source=source,
        evidence_text="external evidence",
        verified_at="2026-09-02T00:00:00+00:00",
    )


def test_verified_records_project_to_skills():
    projection = build_verified_profile_projection(
        (
            verified(
                1,
                "Python",
                "dec_1",
                "job_1",
                "email",
            ),
            verified(
                2,
                "Python",
                "dec_2",
                "job_2",
                "portal",
            ),
        )
    )

    assert len(projection.skills) == 1
    assert projection.skills[0].skill == "Python"
    assert projection.skills[0].verified_evidence_count == 2
    assert set(
        projection.skills[0].verified_decision_ids
    ) == {"dec_1", "dec_2"}
    assert set(
        projection.skills[0].verified_sources
    ) == {"email", "portal"}


def test_empty_verified_records_produce_empty_projection():
    projection = build_verified_profile_projection(())

    assert projection.skills == ()


def test_projection_contains_only_verified_records():
    rejected = VerificationRecord(
        verification_id=3,
        proposal_id=3,
        decision_id="dec_3",
        job_id="job_3",
        skill="Docker",
        status=VerificationStatus.REJECTED,
        verifier_note="rejected",
        evidence_source="email",
        evidence_text="not sufficient",
        verified_at="2026-09-02T00:00:00+00:00",
    )

    projection = build_verified_profile_projection(
        (rejected,)
    )

    assert projection.skills == ()
