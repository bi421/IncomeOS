from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from incomeos.skills.aggregator import build_master_profile, save_master_profile


VERIFIED_EVIDENCE = [
    {
        "id": "incomeos-ci-automation",
        "claim": "The repository contains automated CI tests for regression validation.",
        "source": ".github/workflows/tests.yml; tests/",
    },
    {
        "id": "incomeos-shell-risk",
        "claim": "Repository history documents a fix that removed a shell=True risk surface.",
        "source": "README.md; commit 50e5c2d",
    },
    {
        "id": "incomeos-python-structure",
        "claim": "The repository skill profile documents Python module/package structuring as a proven capability.",
        "source": "README.md; docs/skill_profile.md",
    },
]


def main() -> None:
    repository_root = PROJECT_ROOT / "data" / "github_repos"
    output = PROJECT_ROOT / "data" / "profile" / "master_skill_profile.json"

    profile = build_master_profile(repository_root)
    saved_path = save_master_profile(profile, output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["verified_evidence"] = VERIFIED_EVIDENCE
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"REPOSITORIES: {profile.repository_count}")
    print(f"SKILL_RECORDS: {profile.skill_record_count}")
    print(f"UNIQUE_SKILLS: {len(profile.skills)}")
    print(f"SAVED: {saved_path}")
    print()
    print("MASTER SKILLS")
    print("=============")

    for skill in profile.skills:
        repositories = ", ".join(skill.repositories)
        print(
            f"{skill.name}: {skill.confidence:.2f} "
            f"(evidence={skill.evidence_count}; repos={repositories})"
        )


if __name__ == "__main__":
    main()
