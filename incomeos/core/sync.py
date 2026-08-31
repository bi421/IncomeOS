from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .github import GitHubRepository, list_repositories, sync_repository


@dataclass(frozen=True)
class SyncResult:
    repository: GitHubRepository
    local_path: Path


def sync_all_repositories(
    owner: str,
    destination: str | Path,
    limit: int = 100,
) -> tuple[SyncResult, ...]:
    repositories = list_repositories(owner, limit=limit)

    eligible = tuple(
        repository
        for repository in repositories
        if not repository.is_fork
        and not repository.is_archived
    )

    results = []

    for repository in eligible:
        local_path = sync_repository(
            repository,
            destination,
        )

        results.append(
            SyncResult(
                repository=repository,
                local_path=local_path,
            )
        )

    return tuple(results)