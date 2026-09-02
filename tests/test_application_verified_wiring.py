
from pathlib import Path

from incomeos.applications import engine
from incomeos.skills.verification import VerificationStore


def test_application_uses_only_verified_skill_claims(
    monkeypatch,
    tmp_path,
):
    job = {
        "id": 9001,
        "title": "Python Engineer",
        "url": "https://example.test/jobs/9001",
        "company": "Example Co",
    }

    monkeypatch.setattr(
        engine,
        "get_jobs_by_skill",
        lambda *args, **kwargs: [job],
    )

    captured = {}

    def fake_cover_letter(
        title,
        company,
        skills,
    ):
        captured["skills"] = tuple(skills)
        return "cover letter"

    monkeypatch.setattr(
        engine,
        "generate_cover_letter",
        fake_cover_letter,
    )

    result = engine.apply_to_jobs(
        "Python",
        open_browser=False,
        data_dir=tmp_path,
    )

    assert len(result) == 1
    assert captured["skills"] == ()


def test_verified_skill_is_passed_to_application_content(
    monkeypatch,
    tmp_path,
):
    job = {
        "id": 9002,
        "title": "Python Engineer",
        "url": "https://example.test/jobs/9002",
        "company": "Example Co",
    }

    monkeypatch.setattr(
        engine,
        "get_jobs_by_skill",
        lambda *args, **kwargs: [job],
    )

    captured = {}

    def fake_cover_letter(
        title,
        company,
        skills,
    ):
        captured["skills"] = tuple(skills)
        return "verified cover letter"

    monkeypatch.setattr(
        engine,
        "generate_cover_letter",
        fake_cover_letter,
    )

    verification = VerificationStore(
        tmp_path / "verification.db"
    )

    verification.verify(
        proposal_id=9002,
        decision_id="dec_9002",
        job_id="9002",
        skill="Python",
        evidence_source="human_review",
        evidence_text="Verified Python outcome.",
    )

    result = engine.apply_to_jobs(
        "Python",
        open_browser=False,
        data_dir=tmp_path,
    )

    assert len(result) == 1
    assert captured["skills"] == ("Python",)


def test_unverified_requested_skill_is_not_claimed(
    monkeypatch,
    tmp_path,
):
    job = {
        "id": 9003,
        "title": "Docker Engineer",
        "url": "https://example.test/jobs/9003",
        "company": "Example Co",
    }

    monkeypatch.setattr(
        engine,
        "get_jobs_by_skill",
        lambda *args, **kwargs: [job],
    )

    captured = {}

    def fake_cover_letter(
        title,
        company,
        skills,
    ):
        captured["skills"] = tuple(skills)
        return "generic cover letter"

    monkeypatch.setattr(
        engine,
        "generate_cover_letter",
        fake_cover_letter,
    )

    engine.apply_to_jobs(
        "Docker",
        open_browser=False,
        data_dir=tmp_path,
    )

    assert captured["skills"] == ()


def test_application_state_remains_truthful(
    monkeypatch,
    tmp_path,
):
    job = {
        "id": 9004,
        "title": "Python Engineer",
        "url": "https://example.test/jobs/9004",
        "company": "Example Co",
    }

    monkeypatch.setattr(
        engine,
        "get_jobs_by_skill",
        lambda *args, **kwargs: [job],
    )

    monkeypatch.setattr(
        engine,
        "generate_cover_letter",
        lambda *args, **kwargs: "cover",
    )

    result = engine.apply_to_jobs(
        "Python",
        open_browser=False,
        data_dir=tmp_path,
    )

    assert result[0].status == "PREPARED"
    assert result[0].status != "SUBMITTED"
