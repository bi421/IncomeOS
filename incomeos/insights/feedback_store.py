
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from incomeos.insights.feedback import identify_feedback_signals
from incomeos.tracking.outcomes import (
    OutcomeRecord,
    OutcomeType,
)


@dataclass(frozen=True)
class ProfileUpdateProposal:
    proposal_id: int | None
    decision_id: str
    job_id: str
    skill: str
    proposed_change: str
    basis_outcome: OutcomeType
    evidence_source: str
    evidence_text: str
    status: str
    created_at: str


@dataclass(frozen=True)
class FeedbackRecord:
    feedback_id: int | None
    decision_id: str
    job_id: str
    signals: tuple[str, ...]
    proposal_ids: tuple[int, ...]
    created_at: str


class FeedbackStore:
    def __init__(
        self,
        db_path: str | Path = "data/feedback.db",
    ) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        conn = self._connect()

        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    signals TEXT NOT NULL,
                    proposal_ids TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS profile_update_proposals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    skill TEXT NOT NULL,
                    proposed_change TEXT NOT NULL,
                    basis_outcome TEXT NOT NULL,
                    evidence_source TEXT NOT NULL,
                    evidence_text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            conn.commit()
        finally:
            conn.close()

    def save_proposal(
        self,
        proposal: ProfileUpdateProposal,
    ) -> int:
        conn = self._connect()

        try:
            cursor = conn.execute(
                """
                INSERT INTO profile_update_proposals (
                    decision_id,
                    job_id,
                    skill,
                    proposed_change,
                    basis_outcome,
                    evidence_source,
                    evidence_text,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal.decision_id,
                    proposal.job_id,
                    proposal.skill,
                    proposal.proposed_change,
                    proposal.basis_outcome.value,
                    proposal.evidence_source,
                    proposal.evidence_text,
                    proposal.status,
                    proposal.created_at,
                ),
            )

            conn.commit()
            return int(cursor.lastrowid)
        finally:
            conn.close()

    def save_feedback(
        self,
        feedback: FeedbackRecord,
    ) -> int:
        conn = self._connect()

        try:
            cursor = conn.execute(
                """
                INSERT INTO feedback (
                    decision_id,
                    job_id,
                    signals,
                    proposal_ids,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    feedback.decision_id,
                    feedback.job_id,
                    json.dumps(
                        list(feedback.signals),
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        list(feedback.proposal_ids),
                    ),
                    feedback.created_at,
                ),
            )

            conn.commit()
            return int(cursor.lastrowid)
        finally:
            conn.close()

    def list_proposals(
        self,
        decision_id: str,
    ) -> tuple[ProfileUpdateProposal, ...]:
        conn = self._connect()

        try:
            rows = conn.execute(
                """
                SELECT
                    id,
                    decision_id,
                    job_id,
                    skill,
                    proposed_change,
                    basis_outcome,
                    evidence_source,
                    evidence_text,
                    status,
                    created_at
                FROM profile_update_proposals
                WHERE decision_id=?
                ORDER BY id
                """,
                (decision_id,),
            ).fetchall()
        finally:
            conn.close()

        return tuple(
            ProfileUpdateProposal(
                proposal_id=int(row[0]),
                decision_id=row[1],
                job_id=row[2],
                skill=row[3],
                proposed_change=row[4],
                basis_outcome=OutcomeType(row[5]),
                evidence_source=row[6],
                evidence_text=row[7],
                status=row[8],
                created_at=row[9],
            )
            for row in rows
        )


def build_feedback(
    *,
    decision_id: str,
    job_id: str,
    outcomes: Iterable[OutcomeRecord],
    skills: Iterable[str] = (),
    store: FeedbackStore | None = None,
) -> FeedbackRecord:
    """
    Convert observed outcomes into auditable feedback.

    IMPORTANT:
    One verified positive outcome creates exactly ONE proposal.

    Skill attribution is NOT automatically inferred from the outcome.
    When multiple skills are supplied, the proposal explicitly asks for
    human skill attribution.
    """

    if store is None:
        store = FeedbackStore()

    outcomes = tuple(outcomes)
    skills = tuple(
        skill.strip()
        for skill in skills
        if skill.strip()
    )

    signals = tuple(
        identify_feedback_signals(
            outcomes
        )
    )

    proposal_ids: list[int] = []

    relevant_outcomes = [
        outcome
        for outcome in outcomes
        if outcome.outcome_type in {
            OutcomeType.INTERVIEW,
            OutcomeType.OFFER,
        }
        and outcome.evidence_source.strip()
    ]

    for outcome in relevant_outcomes:
        if len(skills) == 1:
            proposed_skill = skills[0]
        else:
            proposed_skill = (
                "REQUIRES_HUMAN_SKILL_ATTRIBUTION"
            )

        proposal = ProfileUpdateProposal(
            proposal_id=None,
            decision_id=decision_id,
            job_id=job_id,
            skill=proposed_skill,
            proposed_change=(
                "review whether this verified outcome "
                "supports increasing evidence strength"
            ),
            basis_outcome=outcome.outcome_type,
            evidence_source=outcome.evidence_source,
            evidence_text=outcome.evidence_text,
            status="PENDING_HUMAN_VERIFICATION",
            created_at=datetime.now(
                timezone.utc
            ).isoformat(),
        )

        proposal_ids.append(
            store.save_proposal(
                proposal
            )
        )

    feedback = FeedbackRecord(
        feedback_id=None,
        decision_id=decision_id,
        job_id=job_id,
        signals=signals,
        proposal_ids=tuple(proposal_ids),
        created_at=datetime.now(
            timezone.utc
        ).isoformat(),
    )

    feedback_id = store.save_feedback(feedback)

    return FeedbackRecord(
        feedback_id=feedback_id,
        decision_id=feedback.decision_id,
        job_id=feedback.job_id,
        signals=feedback.signals,
        proposal_ids=feedback.proposal_ids,
        created_at=feedback.created_at,
    )
