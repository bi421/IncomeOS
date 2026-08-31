from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from incomeos.skills.aggregator import (
    build_master_profile,
    save_master_profile,
)


def main() -> None:
    repository_root = (
        PROJECT_ROOT
        / "data"
        / "github_repos"
    )

    output = (
        PROJECT_ROOT
        / "data"
        / "profile"
        / "master_skill_profile.json"
    )

    profile = build_master_profile(
        repository_root
    )

    saved_path = save_master_profile(
        profile,
        output,
    )

    print(
        f"REPOSITORIES: {profile.repository_count}"
    )

    print(
        f"SKILL_RECORDS: {profile.skill_record_count}"
    )

    print(
        f"UNIQUE_SKILLS: {len(profile.skills)}"
    )

    print(
        f"SAVED: {saved_path}"
    )

    print()
    print("MASTER SKILLS")
    print("=============")

    for skill in profile.skills:
        repositories = ", ".join(
            skill.repositories
        )

        print(
            f"{skill.name}: "
            f"{skill.confidence:.2f} "
            f"(evidence={skill.evidence_count}; "
            f"repos={repositories})"
        )


if __name__ == "__main__":
    main()