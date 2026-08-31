from incomeos.skills.profile import build_bold_profile


def test_profile_contains_real_skills():
    profile = build_bold_profile()

    names = {skill.name for skill in profile}

    assert "Python" in names
    assert "Data Engineering" in names
    assert "C++" in names
    assert "Testing" in names
    assert "Flask" in names


def test_skill_evidence_is_bounded():
    profile = build_bold_profile()

    for skill in profile:
        assert 0.0 <= skill.evidence_strength <= 1.0