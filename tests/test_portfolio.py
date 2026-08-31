from incomeos.skills.portfolio import build_portfolio


def test_build_portfolio(tmp_path):
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

    (repo2 / "main.cpp").write_text(
        "int main() {}",
        encoding="utf-8",
    )

    report = build_portfolio(tmp_path)

    assert report.repository_count == 2
    assert report.total_skill_count >= 2