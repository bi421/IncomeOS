
from __future__ import annotations

import argparse

from incomeos.tracking.outcome_service import ingest_external_outcome
from incomeos.tracking.outcomes import OutcomeType


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Record an externally evidenced IncomeOS outcome."
    )

    parser.add_argument("--decision-id", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument(
        "--outcome",
        required=True,
        choices=[
            OutcomeType.SUBMITTED.value,
            OutcomeType.RESPONSE.value,
            OutcomeType.INTERVIEW.value,
            OutcomeType.REJECTION.value,
            OutcomeType.OFFER.value,
            OutcomeType.WITHDRAWN.value,
        ],
    )
    parser.add_argument("--source", required=True)
    parser.add_argument("--text", required=True)

    args = parser.parse_args()

    result = ingest_external_outcome(
        decision_id=args.decision_id,
        job_id=args.job_id,
        outcome_type=OutcomeType(args.outcome),
        evidence_source=args.source,
        evidence_text=args.text,
    )

    print("OUTCOME RECORDED")
    print(f"outcome_id={result.outcome_id}")
    print(f"decision_id={result.decision_id}")
    print(f"job_id={result.job_id}")
    print(f"outcome={result.outcome_type.value}")
    print(f"source={result.evidence_source}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
