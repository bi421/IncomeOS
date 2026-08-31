from incomeos.skills.profile_builder import build_profile


def test_profile_builder(tmp_path):
    (tmp_path / "main.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    report = build_profile(str(tmp_path))

    assert report.skill_count >= 1

    names = {skill.name for skill in report.skills}

    assert "Python" in names