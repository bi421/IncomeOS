from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class InterviewItem:
    """One evidence-grounded interview question and STAR answer."""

    skill: str
    question: str
    answer: str
    evidence_ids: tuple[str, ...]


def load_profile(path: str | Path) -> dict[str, Any]:
    """Load the master skill profile."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("profile must be a JSON object")
    return data


def extract_requirements(job_description: str) -> tuple[str, ...]:
    """Extract known profile skill names mentioned in the target JD."""
    if not job_description.strip():
        raise ValueError("job_description must not be empty")
    text = job_description.lower()
    profile_skills = ("Python", "Testing", "Data Engineering", "C++", "Docker", "CMake")
    return tuple(skill for skill in profile_skills if skill.lower() in text)


def _claims(profile: dict[str, Any]) -> tuple[dict[str, str], ...]:
    raw = profile.get("verified_evidence", [])
    if not isinstance(raw, list):
        return ()
    result: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, dict) and item.get("id") and item.get("claim"):
            result.append(
                {
                    "id": str(item["id"]),
                    "claim": str(item["claim"]),
                    "source": str(item.get("source", "")),
                }
            )
    return tuple(result)


def build_interview(
    job_description: str,
    profile: dict[str, Any],
    count: int = 5,
) -> tuple[InterviewItem, ...]:
    """Build technical questions and STAR answers from documented evidence only."""
    if count < 1:
        raise ValueError("count must be positive")
    skills = extract_requirements(job_description)
    if not skills:
        raw = profile.get("skills", [])
        skills = tuple(
            str(item.get("name"))
            for item in raw
            if isinstance(item, dict) and item.get("name")
        )[:count]

    claims = _claims(profile)
    items: list[InterviewItem] = []
    for skill in skills[:count]:
        relevant = tuple(
            claim for claim in claims
            if skill.lower() in claim["claim"].lower()
        )
        if not relevant:
            relevant = claims[:1]
        ids = tuple(item["id"] for item in relevant)
        evidence = " ".join(
            f'{item["claim"]} (source: {item["source"]})'
            for item in relevant
        )
        answer = (
            f"Situation: The documented repository evidence concerns {skill}.\n"
            f"Task: Only the task details explicitly documented in the evidence can be claimed.\n"
            f"Action: {evidence or 'No verified action evidence is available.'}\n"
            f"Result: No additional result is inferred beyond the documented evidence."
        )
        question = (
            f"Technical question: Explain how you would approach a {skill} problem "
            "in a production Python codebase, and distinguish your verified experience "
            "from what you would need to learn."
        )
        items.append(InterviewItem(skill, question, answer, ids))
    return tuple(items)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evidence-grounded STAR mock interview")
    parser.add_argument("--profile", default="data/profile/master_skill_profile.json")
    parser.add_argument("--jd-file", required=True)
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()

    jd = Path(args.jd_file).read_text(encoding="utf-8")
    items = build_interview(jd, load_profile(args.profile), args.count)
    for index, item in enumerate(items, 1):
        print(f"\n{index}. {item.skill}")
        print(item.question)
        print(item.answer)
        print(f"Evidence IDs: {', '.join(item.evidence_ids) or 'none'}")


if __name__ == "__main__":
    main()
