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
    parser.add_argument("--minimum-fit", type=float, default=0.70)
    parser.add_argument("--target-country", default="Mongolia")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--profile", default="data/profile/master_skill_profile.json")
    args = parser.parse_args()

    profile_root = Path("data/github_repos")
    if not profile_root.exists():
        raise SystemExit("missing data/github_repos evidence fixture")

    profile = build_master_profile(profile_root)
    skills = tuple(
        str(item.get("name", "")).strip()
        for item in profile.skills
        if isinstance(item, dict) and float(item.get("confidence", 0.0)) >= 0.60
    )
    hunter = JobHunter(args.data_dir)
    report = hunter.hunt(skills, limit=args.limit, minimum_fit=args.minimum_fit)

    generator = EvidenceBoundGenerator(args.profile)
    queue = ApplicationQueue(Path(args.data_dir) / "application_queue.db")

    ready = []
    for item in report.items:
        job = Job(
            source=item.source,
            title=item.title,
            source_url=item.url,
            company=item.company,
            description=item.description,
            raw_data={"location": item.location},
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
        if prepared is not None:
            ready.append(prepared)

    print("APPLICATION-READY JOBS")
    print("======================")
    print(json.dumps([
        {
            "title": x.title,
            "company": x.company,
            "fit_score": x.fit_score,
            "eligibility": x.eligibility.status,
            "url": x.url,
            "status": x.status,
        }
        for x in ready
    ], ensure_ascii=False, indent=2))
    print(f"READY_COUNT={len(ready)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
