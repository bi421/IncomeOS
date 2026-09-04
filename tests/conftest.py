from pathlib import Path

import pytest


@pytest.fixture
def github_repos_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "github_repos"
    repo = root / "sample_project"
    (repo / ".git").mkdir(parents=True)
    (repo / "tests").mkdir()

    (repo / ".git" / "HEAD").write_text(
        "ref: refs/heads/main\n",
        encoding="utf-8",
    )
    (repo / "app.py").write_text(
        "def run():\n    return 'ok'\n",
        encoding="utf-8",
    )
    (repo / "data_pipeline.py").write_text(
        "def load_data():\n    return []\n",
        encoding="utf-8",
    )
    (repo / "Dockerfile").write_text(
        "FROM python:3.12-slim\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_smoke.py").write_text(
        "def test_smoke():\n    assert True\n",
        encoding="utf-8",
    )

    return root
