
from __future__ import annotations

import argparse

from incomeos.skills.verification import VerificationStore


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify an IncomeOS profile-update proposal."
    )

    parser.add_argument("--proposal-id", required=True, type=int)
    parser.add_argument("--decision-id", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--note", default="")

    args = parser.parse_args()

    record = VerificationStore().verify(
        proposal_id=args.proposal_id,
        decision_id=args.decision_id,
        job_id=args.job_id,
        skill=args.skill,
        evidence_source=args.source,
        evidence_text=args.evidence,
        verifier_note=args.note,
    )

    print("VERIFICATION RECORDED")
    print(f"verification_id={record.verification_id}")
    print(f"proposal_id={record.proposal_id}")
    print(f"skill={record.skill}")
    print(f"status={record.status.value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
