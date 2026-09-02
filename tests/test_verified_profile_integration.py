
from pathlib import Path

from incomeos.skills.aggregator import (
    build_master_profile,
)


def test_verified_evidence_is_optional(tmp_path):
    profile = build_master_profile(
        "data/github_repos"
    )

    assert profile.skills
    assert all(
        skill.verified_evidence_count >= 0
        for skill in profile.skills
    )


def test_verified_evidence_strengthens_existing_skill(
    monkeypatch,
    tmp_path,
):
    from incomeos.skills import aggregator

    class FakeRecord:
        def __init__(
            self,
            skill,
            decision_id,
        ):
            self.skill = skill
            self.decision_id = decision_id

    monkeypatch.setattr(
        aggregator,
        "_load_verified_records",
        lambda _: (
            FakeRecord(
                "Python",
                "dec_verified_1",
            ),
        ),
    )

    profile = build_master_profile(
        "data/github_repos"
    )

    python = next(
        skill
        for skill in profile.skills
        if skill.name == "Python"
    )

    assert python.verified_evidence_count == 1
    assert python.verified_decision_ids == (
        "dec_verified_1",
    )
    assert python.confidence > 1.0 - 0.001 or python.confidence == 1.0


def test_multiple_verified_records_are_bounded(
    monkeypatch,
):
    from incomeos.skills import aggregator

    class FakeRecord:
        def __init__(
            self,
            skill,
            decision_id,
        ):
            self.skill = skill
            self.decision_id = decision_id

    monkeypatch.setattr(
        aggregator,
        "_load_verified_records",
        lambda _: tuple(
            FakeRecord(
                "C++",
                f"dec_{index}",
            )
            for index in range(20)
        ),
    )

    profile = build_master_profile(
        "data/github_repos"
    )

    cpp = next(
        skill
        for skill in profile.skills
        if skill.name == "C++"
    )

    assert cpp.verified_evidence_count == 20
    assert cpp.confidence <= 1.0
    assert len(cpp.verified_decision_ids) == 20


def test_unverified_new_skill_is_not_created(
    monkeypatch,
):
    from incomeos.skills import aggregator

    class FakeRecord:
        skill = "ImaginarySkill"
        decision_id = "dec_fake"

    monkeypatch.setattr(
        aggregator,
        "_load_verified_records",
        lambda _: (FakeRecord(),),
    )

    profile = build_master_profile(
        "data/github_repos"
    )

    names = {
        skill.name
        for skill in profile.skills
    }

    assert "ImaginarySkill" not in names
