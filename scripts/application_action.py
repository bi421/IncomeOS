from __future__ import annotations

import argparse

from incomeos.job_hunt.application_queue import ApplicationQueue
from incomeos.tracking.outcome_service import ingest_external_outcome, ingest_local_application_state
from incomeos.tracking.outcomes import OutcomeType
from incomeos.tracking.tracker import ApplicationStatus, ApplicationTracker


def main() -> int:
    parser = argparse.ArgumentParser(description="Human-controlled application action recorder.")
    parser.add_argument("action", choices=("approve", "open", "submitted"))
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--decision-id", default="job-hunt")
    parser.add_argument("--evidence-source", default="")
    parser.add_argument("--evidence-text", default="")
    args = parser.parse_args()

    queue = ApplicationQueue()
    tracker = ApplicationTracker()

    if args.action == "approve":
        result = queue.approve(args.job_id, tracker)
        print(f"APPROVED | {result.title} | {result.company} | {result.url}")
        return 0

    if queue.status(args.job_id) != "APPROVED":
        raise SystemExit("job must be APPROVED before an external application action")

    if args.action == "open":
        ingest_local_application_state(
            decision_id=args.decision_id,
            job_id=args.job_id,
            state=OutcomeType.OPENED_IN_BROWSER,
        )
        print(f"OPENED_IN_BROWSER | {args.job_id}")
        print(f"URL={args.job_id}")
        return 0

    if not args.evidence_source.strip() or not args.evidence_text.strip():
        raise SystemExit("submitted requires --evidence-source and --evidence-text")
    ingest_external_outcome(
        decision_id=args.decision_id,
        job_id=args.job_id,
        outcome_type=OutcomeType.SUBMITTED,
        evidence_source=args.evidence_source,
        evidence_text=args.evidence_text,
    )
    tracker.transition(args.job_id, ApplicationStatus.APPLIED, args.evidence_source)
    print(f"SUBMITTED_RECORDED | {args.job_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
