from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import EvidenceDimension


@dataclass(frozen=True)
class EvidenceRecord:
    repository: str
    source: str
    evidence_type: str
    dimension: EvidenceDimension
    detail: str


def build_evidence_ledger(
    repository_path: str | Path,
) -> tuple[EvidenceRecord, ...]:
    from .github_analyzer import analyze_repository

    evidence = analyze_repository(repository_path)

    return tuple(
        EvidenceRecord(
            repository=item.repository,
            source=item.source,
            evidence_type=item.evidence_type,
            dimension=item.dimension,
            detail=item.detail,
        )
        for item in evidence
    )


def build_portfolio_evidence_ledger(
    root: str | Path,
) -> tuple[EvidenceRecord, ...]:
    root_path = Path(root)

    records: list[EvidenceRecord] = []

    for repository in sorted(root_path.iterdir()):
        if not repository.is_dir():
            continue

        if not (repository / ".git").exists():
            continue

        records.extend(
            build_evidence_ledger(repository)
        )

    return tuple(records)
