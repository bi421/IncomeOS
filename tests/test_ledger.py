from pathlib import Path

from incomeos.skills.ledger import (
    EvidenceRecord,
    build_evidence_ledger,
    build_portfolio_evidence_ledger,
)
from incomeos.skills.models import EvidenceDimension


def test_evidence_ledger_preserves_source(tmp_path):
    (tmp_path / "main.py").write_text(
        "def hello():\n    return 'world'\n",
        encoding="utf-8",
    )

    ledger = build_evidence_ledger(tmp_path)

    assert len(ledger) == 1
    assert isinstance(ledger[0], EvidenceRecord)
    assert ledger[0].source == "main.py"
    assert ledger[0].dimension == EvidenceDimension.IMPLEMENTATION


def test_evidence_ledger_preserves_multiple_files(tmp_path):
    (tmp_path / "a.py").write_text(
        "print('a')\n",
        encoding="utf-8",
    )

    (tmp_path / "b.py").write_text(
        "print('b')\n",
        encoding="utf-8",
    )

    ledger = build_evidence_ledger(tmp_path)

    sources = {item.source for item in ledger}

    assert sources == {"a.py", "b.py"}


def test_portfolio_ledger_preserves_repository_identity(tmp_path):
    repo1 = tmp_path / "repo1"
    repo2 = tmp_path / "repo2"

    repo1.mkdir()
    repo2.mkdir()

    (repo1 / ".git").mkdir()
    (repo2 / ".git").mkdir()

    (repo1 / "main.py").write_text(
        "print('one')\n",
        encoding="utf-8",
    )

    (repo2 / "main.cpp").write_text(
        "int main() { return 0; }\n",
        encoding="utf-8",
    )

    ledger = build_portfolio_evidence_ledger(tmp_path)

    repositories = {
        item.repository
        for item in ledger
    }

    assert repositories == {"repo1", "repo2"}


def test_portfolio_ledger_is_deterministic(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    for name in ("z.py", "a.py", "m.py"):
        (repo / name).write_text(
            "print('x')\n",
            encoding="utf-8",
        )

    ledger1 = build_portfolio_evidence_ledger(tmp_path)
    ledger2 = build_portfolio_evidence_ledger(tmp_path)

    assert ledger1 == ledger2
    assert [
        item.source
        for item in ledger1
    ] == [
        "a.py",
        "m.py",
        "z.py",
    ]
