from __future__ import annotations

import argparse
import json
from pathlib import Path

from incomeos.applications.generator import EvidenceBoundGenerator
from incomeos.job_hunt.eligibility import assess_eligibility
from incomeos.job_hunt.hunter import JobHunter
from incomeos.job_hunt.application_queue import ApplicationQueue
from incomeos.skills.aggregator import build_master_profile
from incomeos.jobs.models.job import Job


def main() -> int:
    parser = argparse.ArgumentParser(description="Build human-reviewable application-ready packages.")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--ready-limit", type=int, default=3)
    parser.add_argument("--minimum-fit", type=float, default=0.70)
    parser.add_argument("--target-country", default="Mongolia")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--profile", default="data/profile/master_skill_profile.json")
    args = parser.parse_args()

    if not 0.0 <= args.minimum_fit <= 1.0:
        raise SystemExit("--minimum-fit must be between 0 and 1")
    if args.ready_limit < 1:
        raise SystemExit("--ready-limit must be >= 1")

    profile_root = Path("data/github_repos")
    if not profile_root.exists():
        raise SystemExit("missing data/github_repos evidence fixture")

    profile = build_master_profile(profile_root)
    eligible_profile_skills = tuple(
        skill
        for skill in profile.skills
        if skill.name.strip() and skill.confidence >= 0.60
    )
    skills = tuple(skill.name for skill in eligible_profile_skills)
    hunter = JobHunter(args.data_dir)
    report = hunter.hunt(skills, limit=args.limit, minimum_fit=args.minimum_fit)

    generator = EvidenceBoundGenerator(args.profile)
    queue = ApplicationQueue(Path(args.data_dir) / "application_queue.db")

    ready: list[dict[str, object]] = []
    for item in report.items:
        job = Job(
            source=item.source,
            title=item.title,
            source_url=item.url,
            company=item.company,
            description=item.description,
            raw_data=item.raw_data,
        )
        eligibility = assess_eligibility(job, args.target_country)
        if eligibility.status != "PASS":
            continue

        prepared = queue.prepare(
            job=job,
            fit_score=item.fit_score,
            eligibility=eligibility,
            generator=generator,
        )
        if prepared is None:
            continue

        matched_modes = {
            skill.name: skill.evidence_mode
            for skill in eligible_profile_skills
            if skill.name in item.matched_skills
        }

        ready.append(
            {
                "title": prepared.title,
                "company": prepared.company,
                "source": item.source,
                "location": item.location,
                "fit_score": prepared.fit_score,
                "matched_skills": list(item.matched_skills),
                "matched_skill_modes": matched_modes,
                "missing_skills": list(item.missing_skills),
                "eligibility": prepared.eligibility.status,
                "eligibility_reason": prepared.eligibility.reason,
                "url": prepared.url,
                "status": prepared.status,
                "claim_ids": list(prepared.application.claim_ids),
                "cover_letter": prepared.application.cover_letter,
                "resume_summary": prepared.application.resume_summary,
            }
        )
        if len(ready) >= args.ready_limit:
            break

    payload = {
        "target_country": args.target_country,
        "minimum_fit": args.minimum_fit,
        "ready_limit": args.ready_limit,
        "profile_truth_policy": (
            "Repository evidence is AI-assisted unless separately verified; "
            "confidence does not imply independent mastery."
        ),
        "sources_failed": list(report.failed_sources),
        "total_fetched": report.total_fetched,
        "ready_count": len(ready),
        "jobs": ready,
    }

    print("APPLICATION-READY REVIEW ARTIFACT")
    print("=================================")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"READY_COUNT={len(ready)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
