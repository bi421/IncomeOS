
from incomeos.skills.provenance import (
    build_file_provenance,
    file_content_hash,
)


def test_file_hash_is_stable(tmp_path):
    path = tmp_path / "evidence.txt"

    path.write_text(
        "IncomeOS evidence",
        encoding="utf-8",
    )

    assert file_content_hash(path) == file_content_hash(path)


def test_provenance_contains_traceable_fields(tmp_path):
    repository = tmp_path / "repo"
    repository.mkdir()

    path = repository / "main.py"
    path.write_text(
        "print('ok')",
        encoding="utf-8",
    )

    record = build_file_provenance(
        repository=repository,
        source_path=path,
        source_type="source_file",
    )

    assert record.repository == "repo"
    assert record.source_path == str(path)
    assert len(record.content_hash) == 64
    assert record.source_ref
