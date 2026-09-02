
from __future__ import annotations

from pathlib import Path
import tempfile

from incomeos.decision.persistence import DecisionStore
from incomeos.decision.service import evaluate_and_persist
from incomeos.insights.feedback_store import (
    FeedbackStore,
    build_feedback,
)
from incomeos.jobs.fit import (
    JobRequirement,
    evaluate_job_fit,
)
from incomeos.skills.levels import CapabilityLevel
from incomeos.skills.verification import VerificationStore
from incomeos.tracking.outcome_service import ingest_external_outcome
from incomeos.tracking.outcomes import OutcomeStore, OutcomeType


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        profile = {
            "capabilities": [
                {
                    "name": "Python Application Development",
                    "skills": ["Python"],
                    "confidence": 0.95,
                    "level": "A",
                }
            ]
        }

        fit = evaluate_job_fit(
            job_id="dry-job-001",
            requirements=(
                JobRequirement(
                    "Python",
                    CapabilityLevel.B,
                ),
            ),
            profile=profile,
        )

        assert fit.is_qualified
        assert fit.fit_score == 1.0

        decisions = DecisionStore(
            root / "decisions.db"
        )

        decision = evaluate_and_persist(
            fit=fit,
            opportunity_name="Python Automation",
            store=decisions,
        )

        assert decision.record.decision == "APPLY"

        outcomes = OutcomeStore(
            root / "outcomes.db"
        )

        ingest_external_outcome(
            decision_id=decision.record.decision_id,
            job_id="dry-job-001",
            outcome_type=OutcomeType.INTERVIEW,
            evidence_source="synthetic-evidence",
            evidence_text="Synthetic interview evidence.",
            store=outcomes,
        )

        observed = outcomes.list_for_decision(
            decision.record.decision_id
        )

        feedback_store = FeedbackStore(
            root / "feedback.db"
        )

        feedback = build_feedback(
            decision_id=decision.record.decision_id,
            job_id="dry-job-001",
            outcomes=observed,
            skills=("Python",),
            store=feedback_store,
        )

        assert len(feedback.proposal_ids) == 1

        verification = VerificationStore(
            root / "verification.db"
        )

        verified = verification.verify(
            proposal_id=feedback.proposal_ids[0],
            decision_id=decision.record.decision_id,
            job_id="dry-job-001",
            skill="Python",
            evidence_source="synthetic-human-review",
            evidence_text="Synthetic verified attribution.",
            verifier_note="Dry-run verification.",
        )

        records = verification.list_verified()

        assert verified.verification_id is not None
        assert len(records) == 1
        assert records[0].skill == "Python"

        print("INCOMEOS END-TO-END DRY RUN")
        print("===========================")
        print("JOB FIT       : PASS")
        print("DECISION      : PASS")
        print("OUTCOME       : PASS")
        print("FEEDBACK      : PASS")
        print("VERIFICATION  : PASS")
        print("PROFILE INPUT : PASS")
        print("DRY RUN RESULT: PASS")


if __name__ == "__main__":
    run()
