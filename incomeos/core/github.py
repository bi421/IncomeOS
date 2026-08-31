from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitHubRepository:
    name: str
    url: str
    is_private: bool
    is_fork: bool
    is_archived: bool


def list_repositories(
    owner: str,
    limit: int = 100,
) -> tuple[GitHubRepository, ...]:
    gh = _find_gh()

    result = subprocess.run(
    [
        gh,
        "repo",
        "list",
        owner,
        "--limit",
        str(limit),
        "--json",
        "name,isPrivate,isFork,isArchived,url",
    ],
    check=True,
    capture_output=True,
    text=True,
    stdin=subprocess.DEVNULL,
)

    payload = json.loads(result.stdout)

    return tuple(
        GitHubRepository(
            name=item["name"],
            url=item["url"],
            is_private=item["isPrivate"],
            is_fork=item["isFork"],
            is_archived=item["isArchived"],
        )
        for item in payload
    )


def sync_repository(
    repository: GitHubRepository,
    destination: str | Path,
) -> Path:
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)

    target = root / repository.name

    if (target / ".git").exists():
        subprocess.run(
            [
                "git",
                "-C",
                str(target),
                "pull",
                "--ff-only",
            ],
            check=True,
            stdin=subprocess.DEVNULL,
        )
    else:
        subprocess.run(
            [
                "git",
                "clone",
                repository.url,
                str(target),
            ],
            check=True,
            stdin=subprocess.DEVNULL,
        )

    return target


def _find_gh() -> str:
    gh = shutil.which("gh")

    if gh is None:
        raise RuntimeError(
            "GitHub CLI 'gh' was not found on PATH."
        )

    return gh