from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from incomeos.job_hunt import JobHunter
from incomeos.skills.aggregator import build_master_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="IncomeOS real public job hunt")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--minimum-fit", type=float, default=0.0)
    parser.add_argument(
        "--target-country",
        default=None,
        help="Target country; omit to run in global/worldwide mode.",
    )
    args = parser.parse_args()

    if args.limit < 1:
        raise SystemExit("--limit must be >= 1")
    if not 0.0 <= args.minimum_fit <= 1.0:
        raise SystemExit("--minimum-fit must be between 0 and 1")

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
        target_country=args.target_country,
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
        if health.error:
            print(f"SOURCE_ERROR={health.source} {health.error}")

    source_endpoints = {health.source: health.endpoint for health in report.sources}

    for item in report.items:
        matched_modes = tuple(
            skill.evidence_mode
            for skill in eligible_skills
            if skill.name in item.matched_skills
        )
        posted_at = item.raw_data.get("posted_at") or "UNKNOWN"
        posted_age_days = item.raw_data.get("posted_age_days")
        age_text = f"{posted_age_days:.1f}" if isinstance(posted_age_days, (int, float)) else "UNKNOWN"
        print(
            f"JOB | CHECK_SCORE={item.overall_score}/100 | FIT={item.fit_score:.3f} | "
            f"TITLE={item.title} | COMPANY={item.company} | SOURCE={item.source} | "
            f"SOURCE_ENDPOINT={source_endpoints.get(item.source, 'UNKNOWN')} | "
            f"POSTED_AT={posted_at} | AGE_DAYS={age_text} | URL={item.url} | "
            f"MATCHED_MODES={matched_modes}"
        )

    if not report.items:
        print("RESULT=NO_JOBS")
    else:
        print(f"RESULT=JOBS_FOUND COUNT={len(report.items)}")

    # A completely unavailable source set is an operational failure, not
    # evidence that no jobs exist. Partial source failure remains a valid,
    # explicitly visible partial result.
    if report.sources and len(report.failed_sources) == len(report.sources):
        print("RESULT_STATUS=ALL_SOURCES_FAILED")
        return 2

    if report.failed_sources:
        print("RESULT_STATUS=PARTIAL_SOURCE_FAILURE")
    else:
        print("RESULT_STATUS=COMPLETE_SOURCE_SET")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
