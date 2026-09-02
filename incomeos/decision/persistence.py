from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    job_id: str
    opportunity_name: str
    decision: str
    score: float
    reason: str
    evidence_snapshot: tuple[dict[str, Any], ...]
    created_at: str


def _canonical_payload(
    *,
    job_id: str,
    opportunity_name: str,
    decision: str,
    score: float,
    reason: str,
    evidence_snapshot: tuple[dict[str, Any], ...],
) -> str:
    payload = {
        "job_id": str(job_id),
        "opportunity_name": str(opportunity_name),
        "decision": str(decision),
        "score": round(float(score), 8),
        "reason": str(reason),
        "evidence_snapshot": list(evidence_snapshot),
    }

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def stable_decision_id(
    *,
    job_id: str,
    opportunity_name: str,
    decision: str,
    score: float,
    reason: str,
    evidence_snapshot: tuple[dict[str, Any], ...],
) -> str:
    canonical = _canonical_payload(
        job_id=job_id,
        opportunity_name=opportunity_name,
        decision=decision,
        score=score,
        reason=reason,
        evidence_snapshot=evidence_snapshot,
    )

    digest = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    return f"dec_{digest[:24]}"


class DecisionStore:
    def __init__(
        self,
        db_path: str | Path = "data/decisions.db",
    ) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(
            self.db_path
        )

    def _init_db(self) -> None:
        conn = self._connect()

        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    opportunity_name TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    score REAL NOT NULL,
                    reason TEXT NOT NULL,
                    evidence_snapshot TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_decisions_job
                ON decisions(job_id)
                """
            )
            conn.commit()
        finally:
            conn.close()

    def save(
        self,
        record: DecisionRecord,
    ) -> None:
        conn = self._connect()

        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO decisions (
                    decision_id,
                    job_id,
                    opportunity_name,
                    decision,
                    score,
                    reason,
                    evidence_snapshot,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.decision_id,
                    record.job_id,
                    record.opportunity_name,
                    record.decision,
                    record.score,
                    record.reason,
                    json.dumps(
                        list(record.evidence_snapshot),
                        sort_keys=True,
                        ensure_ascii=False,
                    ),
                    record.created_at,
                ),
            )

            conn.commit()
        finally:
            conn.close()

    def get(
        self,
        decision_id: str,
    ) -> DecisionRecord | None:
        conn = self._connect()

        try:
            row = conn.execute(
                """
                SELECT
                    decision_id,
                    job_id,
                    opportunity_name,
                    decision,
                    score,
                    reason,
                    evidence_snapshot,
                    created_at
                FROM decisions
                WHERE decision_id=?
                """,
                (decision_id,),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return None

        return DecisionRecord(
            decision_id=row[0],
            job_id=row[1],
            opportunity_name=row[2],
            decision=row[3],
            score=float(row[4]),
            reason=row[5],
            evidence_snapshot=tuple(
                json.loads(row[6])
            ),
            created_at=row[7],
        )


def create_decision(
    *,
    job_id: str,
    opportunity_name: str,
    decision: str,
    score: float,
    reason: str,
    evidence_snapshot: tuple[dict[str, Any], ...] = (),
) -> DecisionRecord:
    score = max(
        0.0,
        min(1.0, float(score)),
    )

    decision_id = stable_decision_id(
        job_id=job_id,
        opportunity_name=opportunity_name,
        decision=decision,
        score=score,
        reason=reason,
        evidence_snapshot=evidence_snapshot,
    )

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    return DecisionRecord(
        decision_id=decision_id,
        job_id=str(job_id),
        opportunity_name=opportunity_name,
        decision=decision,
        score=score,
        reason=reason,
        evidence_snapshot=evidence_snapshot,
        created_at=created_at,
    )
