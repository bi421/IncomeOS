from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from incomeos.jobs.filters import is_relevant
from incomeos.jobs.requirements import SKILL_ALIASES, clean_html, extract_requirements

API_URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch_jobs() -> list[dict[str, Any]]:
    request = urllib.request.Request(
        API_URL,
        headers={"User-Agent": "IncomeOS/1.0 (+https://github.com/bi421/IncomeOS)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    records = payload.get("data", [])
    if not isinstance(records, list):
        raise ValueError("Arbeitnow response has no data list")
    return [record for record in records if isinstance(record, dict)]


def _aliases(skill: str) -> tuple[str, ...]:
    return SKILL_ALIASES.get(skill, (skill.lower(),))


def _mentioned(skill: str, text: str) -> bool:
    return any(
        re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", text, re.IGNORECASE)
        for alias in _aliases(skill)
    )


def load_profile(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    result: dict[str, dict[str, Any]] = {}
    for item in data.get("skills", []):
        name = str(item.get("name", "")).strip()
        if name:
            result[name] = item
    if not result:
        raise ValueError(f"profile contains no skills: {path}")
    return result


def analyze(record: dict[str, Any], profile: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    title = str(record.get("title", "")).strip()
    description = clean_html(str(record.get("description", "")))
    tags = record.get("tags", [])
    if not title or not record.get("url") or not is_relevant(title, description, tags):
        return None

    # Parse against the complete known vocabulary, not only the user's skills.
    # Otherwise every unknown required skill disappears and the score is inflated.
    available = tuple(SKILL_ALIASES)
    required, preferred = extract_requirements(
        description=description,
        available_skills=available,
    )
    lower = description.lower()
    title_lower = title.lower()
    mentioned = tuple(skill for skill in available if _mentioned(skill, title + "\n" + description))
    # If the advert has explicit required/preferred sections, score those sections.
    # Otherwise, use only explicit mentions and mark the result as lower-confidence.
    evidence_mode = "explicit_sections" if required or preferred else "explicit_mentions_only"
    target = required or mentioned
    matched_required = tuple(skill for skill in required if skill in profile)
    missing_required = tuple(skill for skill in required if skill not in profile)
    matched_preferred = tuple(skill for skill in preferred if skill in profile)
    matched_mentions = tuple(skill for skill in mentioned if skill not in matched_required and skill not in matched_preferred)
    if required:
        fit = len(matched_required) / len(required)
        preferred_fit = len(matched_preferred) / max(1, len(preferred))
        confidence = sum(float(profile[s].get("confidence", 0.0)) for s in matched_required) / max(1, len(matched_required))
        score = fit * 0.60 + preferred_fit * 0.10 + confidence * 0.30
    elif mentioned:
        fit = len(matched_mentions) / len(mentioned)
        score = min(0.55, 0.25 + 0.05 * len(matched_mentions))
    else:
        return None
    timestamp = record.get("created_at")
    if isinstance(timestamp, (int, float)):
        posted_at = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
    else:
        posted_at = str(timestamp or "")
    return {
        "source": "arbeitnow",
        "title": title,
        "company": str(record.get("company_name", "")).strip() or "Unknown",
        "url": str(record["url"]),
        "posted_at": posted_at,
        "location": record.get("location", ""),
        "salary": record.get("salary", ""),
        "evidence_mode": evidence_mode,
        "score": round(float(score), 4),
        "required_profile_skills": list(matched_required),
        "missing_required_skills": list(missing_required),
        "preferred_profile_skills": list(matched_preferred),
        "other_explicit_mentions": list(matched_mentions),
        "declared_required_skills": list(required),
        "declared_preferred_skills": list(preferred),
        "profile_evidence": {
            skill: {
                "confidence": profile[skill].get("confidence"),
                "evidence_count": profile[skill].get("evidence_count"),
                "repositories": profile[skill].get("repositories", []),
            }
            for skill in target
            if skill in profile
        },
        "description_excerpt": re.sub(r"\s+", " ", description)[:500],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and rank real Arbeitnow jobs using verified profile evidence.")
    parser.add_argument("--profile", type=Path, default=ROOT / "data/profile/master_skill_profile.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/real_opportunities.json")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    profile = load_profile(args.profile)
    records = fetch_jobs()
    opportunities = [item for record in records if (item := analyze(record, profile))]
    opportunities.sort(key=lambda item: (item["score"], len(item["required_profile_skills"])), reverse=True)
    opportunities = opportunities[: max(0, args.limit)]
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": API_URL,
        "source_records": len(records),
        "profile": str(args.profile),
        "profile_skills": list(profile),
        "results": opportunities,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Fetched {len(records)} real records from Arbeitnow")
    print(f"Produced {len(opportunities)} evidence-backed opportunities")
    print(f"Wrote {args.output}")
    for index, item in enumerate(opportunities, 1):
        skills = ", ".join(item["profile_evidence"])
        if not skills:
            skills = "no profile evidence"
        print(f"{index:02d}. {item['score']:.0%} | {item['title']} | {item['company']} | {skills} | {item['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
