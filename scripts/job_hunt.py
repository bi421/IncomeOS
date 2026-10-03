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
    eligible_skills = tuple(
        skill
        for skill in profile.skills
        if skill.name.strip() and skill.confidence >= 0.60
    )
    skills = [skill.name for skill in eligible_skills]
    if not skills:
        raise SystemExit("No evidence-backed skills meet the 0.60 confidence threshold.")

    print("PROFILE_TRUTH_POLICY=repository evidence is AI-assisted unless separately verified")
    print("PROFILE_SKILL_MODES:")
    for skill in eligible_skills:
        print(
            f"  {skill.name} | confidence={skill.confidence:.3f} "
            f"| mode={skill.evidence_mode}"
        )

    report = JobHunter(args.data_dir).hunt(
        skills,
        limit=args.limit,
        minimum_fit=args.minimum_fit,
    )
    print(
        f"SOURCES={len(report.sources)} "
        f"FAILED={len(report.failed_sources)} "
        f"FETCHED={report.total_fetched}"
    )
    for health in report.sources:
        print(
            f"SOURCE={health.source} FAILED={health.failed} "
            f"FETCHED={health.fetched} ACCEPTED={health.accepted} "
            f"ACCEPTANCE_RATE={health.acceptance_rate:.3f} "
            f"PROTOCOL={health.protocol} ENDPOINT={health.endpoint} "
            f"OBSERVED_AT={health.observed_at}"
        )
    for item in report.items:
        matched_modes = tuple(
            skill.evidence_mode
            for skill in eligible_skills
            if skill.name in item.matched_skills
        )
        print(
            f"{item.fit_score:.3f} | {item.title} | {item.company} | "
            f"{item.source} | {item.url} | "
            f"MATCHED_MODES={matched_modes}"
        )
    if not report.items:
        print("RESULT=NO_JOBS")
    else:
        print(f"RESULT=JOBS_FOUND COUNT={len(report.items)}")
    # No-jobs is a valid hunt result. Runtime errors still raise and fail the job.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
