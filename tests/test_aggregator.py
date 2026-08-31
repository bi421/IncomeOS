from incomeos.skills.aggregator import (
    DIMENSION_WEIGHTS,
    MasterSkillProfile,
    build_master_profile,
    save_master_profile,
)
from incomeos.skills.models import EvidenceDimension


def test_master_profile_from_portfolio(tmp_path):
    repo1 = tmp_path / "repo1"
    repo2 = tmp_path / "repo2"

    repo1.mkdir()
    repo2.mkdir()

    (repo1 / ".git").mkdir()
    (repo2 / ".git").mkdir()

    (repo1 / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    (repo2 / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    profile = build_master_profile(tmp_path)

    assert isinstance(profile, MasterSkillProfile)
    assert profile.repository_count == 2
    assert profile.skill_record_count >= 2
    assert len(profile.skills) >= 1


def test_save_master_profile(tmp_path):
    profile = MasterSkillProfile(
        repository_count=1,
        skill_record_count=1,
        skills=(),
    )

    output = tmp_path / "profile.json"

    saved = save_master_profile(
        profile,
        output,
    )

    assert saved.exists()

    import json

    payload = json.loads(
        saved.read_text(encoding="utf-8")
    )

    assert payload["repository_count"] == 1
    assert payload["skill_record_count"] == 1
    assert payload["unique_skill_count"] == 0


def test_dimension_weights_are_ordered():
    assert (
        DIMENSION_WEIGHTS[EvidenceDimension.IMPLEMENTATION]
        > DIMENSION_WEIGHTS[EvidenceDimension.VALIDATION]
        > DIMENSION_WEIGHTS[EvidenceDimension.ENGINEERING]
        > DIMENSION_WEIGHTS[EvidenceDimension.USAGE]
        > DIMENSION_WEIGHTS[EvidenceDimension.PRESENCE]
    )


def test_implementation_gets_full_dimension_weight():
    assert (
        DIMENSION_WEIGHTS[EvidenceDimension.IMPLEMENTATION]
        == 1.0
    )


def test_presence_gets_lower_dimension_weight():
    assert (
        DIMENSION_WEIGHTS[EvidenceDimension.PRESENCE]
        < DIMENSION_WEIGHTS[EvidenceDimension.IMPLEMENTATION]
    )
