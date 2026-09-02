
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess


@dataclass(frozen=True)
class EvidenceProvenance:
    source_type: str
    source_ref: str
    source_path: str
    content_hash: str
    repository: str
    git_commit: str
    generated_at: str


def file_content_hash(path: str | Path) -> str:
    digest = hashlib.sha256()

    with Path(path).open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def git_commit(repository: str | Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            capture_output=True,
            text=True,
            check=True,
        )
    except (
        OSError,
        subprocess.CalledProcessError,
    ):
        return ""

    return result.stdout.strip()


def build_file_provenance(
    *,
    repository: str | Path,
    source_path: str | Path,
    source_type: str,
    source_ref: str | None = None,
) -> EvidenceProvenance:
    repository_path = Path(repository)
    source = Path(source_path)

    try:
        relative = source.relative_to(repository_path)
    except ValueError:
        relative = source

    return EvidenceProvenance(
        source_type=source_type,
        source_ref=source_ref or str(relative),
        source_path=str(source),
        content_hash=file_content_hash(source),
        repository=repository_path.name,
        git_commit=git_commit(repository_path),
        generated_at=datetime.now(
            timezone.utc
        ).isoformat(),
    )


def save_provenance_manifest(
    records: list[EvidenceProvenance],
    output: str | Path,
) -> Path:
    target = Path(output)
    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target.write_text(
        json.dumps(
            [asdict(record) for record in records],
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return target
