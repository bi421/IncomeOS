
from incomeos.applications.context import (
    load_application_evidence_context,
    select_verified_skills,
)
from incomeos.skills.verification import VerificationStore


def test_missing_verification_db_is_safe(tmp_path):
    context = load_application_evidence_context(
        tmp_path / "missing.db"
    )

    assert context.verified_skills == ()
    assert context.source_count == 0


def test_verified_skill_is_available_to_application_context(tmp_path):
    db = tmp_path / "verification.db"

    store = VerificationStore(db)

    store.verify(
        proposal_id=1,
        decision_id="dec_1",
        job_id="job_1",
        skill="Python",
        evidence_source="email",
        evidence_text="Verified outcome.",
    )

    context = load_application_evidence_context(db)

    assert context.verified_skills == ("Python",)

    assert select_verified_skills(
        "Python",
        context,
    ) == ("Python",)


def test_unverified_skill_is_not_selected(tmp_path):
    context = load_application_evidence_context(
        tmp_path / "missing.db"
    )

    assert select_verified_skills(
        "Docker",
        context,
    ) == ()
