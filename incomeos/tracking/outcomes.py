from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import json
import sqlite3
from pathlib import Path
from typing import Any


class OutcomeType(StrEnum):
    PREPARED = "PREPARED"
    OPENED_IN_BROWSER = "OPENED_IN_BROWSER"
    SUBMITTED = "SUBMITTED"
    RESPONSE = "RESPONSE"
    INTERVIEW = "INTERVIEW"
    REJECTION = "REJECTION"
    OFFER = "OFFER"
    WITHDRAWN = "WITHDRAWN"
    UNKNOWN = "UNKNOWN"


EXTERNALLY_EVIDENCED = {
    OutcomeType.SUBMITTED,
    OutcomeType.RESPONSE,
    OutcomeType.INTERVIEW,
    OutcomeType.REJECTION,
    OutcomeType.OFFER,
}


@dataclass(frozen=True)
class OutcomeRecord:
    outcome_id: int | None
    decision_id: str
    job_id: str
    outcome_type: OutcomeType
    evidence_source: str
    evidence_text: str
    observed_at: str
    metadata: dict[str, Any]


class OutcomeStore:
    def __init__(
        self,
        db_path: str | Path = "data/outcomes.db",
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
                CREATE TABLE IF NOT EXISTS outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    outcome_type TEXT NOT NULL,
                    evidence_source TEXT NOT NULL,
                    evidence_text TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_outcomes_decision
                ON outcomes(decision_id)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_outcomes_job
                ON outcomes(job_id)
                """
            )

            conn.commit()
        finally:
            conn.close()

    def save(
        self,
        record: OutcomeRecord,
    ) -> int:
        if not record.decision_id.strip():
            raise ValueError(
                "decision_id must not be empty"
            )

        if not record.job_id.strip():
            raise ValueError(
                "job_id must not be empty"
            )

        if (
            record.outcome_type in EXTERNALLY_EVIDENCED
            and not record.evidence_source.strip()
        ):
            raise ValueError(
                "external outcomes require evidence_source"
            )

        conn = self._connect()

        try:
            cursor = conn.execute(
                """
                INSERT INTO outcomes (
                    decision_id,
                    job_id,
                    outcome_type,
                    evidence_source,
                    evidence_text,
                    observed_at,
                    metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.decision_id,
                    record.job_id,
                    record.outcome_type.value,
                    record.evidence_source,
                    record.evidence_text,
                    record.observed_at,
                    json.dumps(
                        record.metadata,
                        sort_keys=True,
                        ensure_ascii=False,
                    ),
                ),
            )

            conn.commit()
            return int(cursor.lastrowid)
        finally:
            conn.close()

    def list_for_decision(
        self,
        decision_id: str,
    ) -> tuple[OutcomeRecord, ...]:
        conn = self._connect()

        try:
            rows = conn.execute(
                """
                SELECT
                    id,
                    decision_id,
                    job_id,
                    outcome_type,
                    evidence_source,
                    evidence_text,
                    observed_at,
                    metadata
                FROM outcomes
                WHERE decision_id=?
                ORDER BY id
                """,
                (decision_id,),
            ).fetchall()
        finally:
            conn.close()

        return tuple(
            OutcomeRecord(
                outcome_id=int(row[0]),
                decision_id=row[1],
                job_id=row[2],
                outcome_type=OutcomeType(row[3]),
                evidence_source=row[4],
                evidence_text=row[5],
                observed_at=row[6],
                metadata=json.loads(row[7]),
            )
            for row in rows
        )


def create_outcome(
    *,
    decision_id: str,
    job_id: str,
    outcome_type: OutcomeType,
    evidence_source: str = "",
    evidence_text: str = "",
    metadata: dict[str, Any] | None = None,
) -> OutcomeRecord:
    if not decision_id.strip():
        raise ValueError(
            "decision_id must not be empty"
        )

    if not job_id.strip():
        raise ValueError(
            "job_id must not be empty"
        )

    if (
        outcome_type in EXTERNALLY_EVIDENCED
        and not evidence_source.strip()
    ):
        raise ValueError(
            "externally evidenced outcomes require evidence_source"
        )

    return OutcomeRecord(
        outcome_id=None,
        decision_id=decision_id,
        job_id=job_id,
        outcome_type=outcome_type,
        evidence_source=evidence_source,
        evidence_text=evidence_text,
        observed_at=datetime.now(
            timezone.utc
        ).isoformat(),
        metadata=metadata or {},
    )
