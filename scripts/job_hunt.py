from __future__ import annotations

import argparse

from incomeos.job_hunt import JobHunter
from incomeos.skills.aggregator import build_master_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="IncomeOS real public job hunt")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--minimum-fit", type=float, default=0.0)
    args = parser.parse_args()

    profile = build_master_profile("data/github_repos")
    skills = [skill.name for skill in profile.skills if skill.confidence >= 0.60]
    if not skills:
        raise SystemExit("No evidence-backed skills meet the 0.60 confidence threshold.")

    report = JobHunter(args.data_dir).hunt(skills, limit=args.limit, minimum_fit=args.minimum_fit)
    print(f"SOURCES={len(report.sources)} FAILED={len(report.failed_sources)} FETCHED={report.total_fetched}")
    for item in report.items:
        print(f"{item.fit_score:.3f} | {item.title} | {item.company} | {item.source} | {item.url}")
    return 1 if not report.items else 0


if __name__ == "__main__":
    raise SystemExit(main())
