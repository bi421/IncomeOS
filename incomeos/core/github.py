from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
import urllib.request
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
    """List repositories without requiring the GitHub CLI.

    The public GitHub API is used by default. If ``GITHUB_TOKEN`` is present,
    it is sent as a bearer token so private repositories visible to the token
    can also be returned.
    """

    if not owner.strip():
        raise ValueError("owner must not be empty")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    encoded_owner = urllib.parse.quote(owner.strip(), safe="")
    query = urllib.parse.urlencode({"per_page": limit})
    url = f"https://api.github.com/users/{encoded_owner}/repos?{query}"

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "IncomeOS",
        },
    )

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise RuntimeError(
            f"GitHub repository listing failed: {exc}"
        ) from exc

    if not isinstance(payload, list):
        raise RuntimeError("GitHub returned an invalid repository payload")

    repositories: list[GitHubRepository] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        repositories.append(
            GitHubRepository(
                name=str(item["name"]),
                url=str(item["html_url"]),
                is_private=bool(item["private"]),
                is_fork=bool(item["fork"]),
                is_archived=bool(item["archived"]),
            )
        )

    return tuple(repositories)


def sync_repository(
    repository: GitHubRepository,
    destination: str | Path,
) -> Path:
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)

    target = root / repository.name

    if (target / ".git").exists():
        subprocess.run(
            ["git", "-C", str(target), "pull", "--ff-only"],
            check=True,
            stdin=subprocess.DEVNULL,
        )
    else:
        subprocess.run(
            ["git", "clone", repository.url, str(target)],
            check=True,
            stdin=subprocess.DEVNULL,
        )

    return target
