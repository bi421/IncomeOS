
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ApplicationEvidenceContext:
    verified_skills: tuple[str, ...]
    verified_decision_ids: tuple[str, ...]
    source_count: int


def load_application_evidence_context(
    db_path: str | Path = "data/verification.db",
) -> ApplicationEvidenceContext:
    path = Path(db_path)

    if not path.exists():
        return ApplicationEvidenceContext(
            verified_skills=(),
            verified_decision_ids=(),
            source_count=0,
        )

    from incomeos.skills.verification import VerificationStore

    records = VerificationStore(path).list_verified()

    return ApplicationEvidenceContext(
        verified_skills=tuple(
            sorted(
                {
                    record.skill
                    for record in records
                    if record.skill.strip()
                }
            )
        ),
        verified_decision_ids=tuple(
            sorted(
                {
                    record.decision_id
                    for record in records
                    if record.decision_id.strip()
                }
            )
        ),
        source_count=len(records),
    )


def select_verified_skills(
    requested_skill: str,
    context: ApplicationEvidenceContext,
) -> tuple[str, ...]:
    skill = requested_skill.strip()

    if not skill:
        return ()

    if skill in context.verified_skills:
        return (skill,)

    return ()
