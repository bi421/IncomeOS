from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from incomeos.core.sync import sync_all_repositories


def main() -> None:
    destination = PROJECT_ROOT / "data" / "github_repos"

    results = sync_all_repositories(
        owner="bi421",
        destination=destination,
    )

    print(f"SYNCED: {len(results)} repositories")

    for result in results:
        print(
            f"{result.repository.name} -> "
            f"{result.local_path}"
        )


if __name__ == "__main__":
    main()