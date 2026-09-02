
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from incomeos.decision.persistence import (
    DecisionRecord,
    DecisionStore,
    create_decision,
)
from incomeos.jobs.fit import (
    JobRequirement,
    JobFit,
    evaluate_job_fit,
)
from incomeos.skills.levels import CapabilityLevel


@dataclass(frozen=True)
class JobDecisionResult:
    job_id: str
    opportunity_name: str
    fit: JobFit
    decision: DecisionRecord


def _normalise_level(
    value: Any,
) -> CapabilityLevel:
    if isinstance(value, CapabilityLevel):
        return value

    try:
        return CapabilityLevel(str(value))
    except (ValueError, TypeError):
        return CapabilityLevel.B


def normalise_job_requirements(
    job: dict[str, Any],
) -> tuple[JobRequirement, ...]:
    """
    Convert a concrete job record into explicit requirements.

    Supported forms:

        {"required_skills": ["Python", "Testing"]}

    or:

        {
            "requirements": [
                {"skill": "Python", "minimum_level": "B"}
            ]
        }

    The normalization is deterministic and does not infer seniority
    from the job title.
    """

    requirements = job.get("requirements")

    if requirements is not None:
        result: list[JobRequirement] = []

        for item in requirements:
            if isinstance(item, str):
                result.append(
                    JobRequirement(
                        item,
                        CapabilityLevel.B,
                    )
                )
                continue

            if isinstance(item, dict):
                skill = str(
                    item.get("skill", "")
                ).strip()

                if not skill:
                    continue

                result.append(
                    JobRequirement(
                        skill,
                        _normalise_level(
                            item.get(
                                "minimum_level",
                                CapabilityLevel.B,
                            )
                        ),
                    )
                )

        return tuple(result)

    required_skills = job.get(
        "required_skills",
        (),
    )

    return tuple(
        JobRequirement(
            str(skill).strip(),
            CapabilityLevel.B,
        )
        for skill in required_skills
        if str(skill).strip()
    )


def evaluate_job(
    *,
    job: dict[str, Any],
    profile: Any,
) -> JobFit:
    job_id = str(
        job.get("id", "")
    ).strip()

    if not job_id:
        raise ValueError(
            "job must contain a non-empty id"
        )

    requirements = normalise_job_requirements(
        job
    )

    return evaluate_job_fit(
        job_id=job_id,
        requirements=requirements,
        profile=profile,
    )


def persist_job_decision(
    *,
    job: dict[str, Any],
    opportunity_name: str,
    profile: Any,
    apply_threshold: float = 1.0,
    store: DecisionStore | None = None,
) -> JobDecisionResult:
    """
    Evaluate and persist a decision for one concrete external job.

    Decision identity is bound to the concrete job ID and the exact
    JobFit evidence snapshot.
    """

    if not opportunity_name.strip():
        raise ValueError(
            "opportunity_name must not be empty"
        )

    if store is None:
        store = DecisionStore()

    fit = evaluate_job(
        job=job,
        profile=profile,
    )

    if not 0.0 <= apply_threshold <= 1.0:
        raise ValueError(
            "apply_threshold must be between 0 and 1"
        )

    decision_name = (
        "APPLY"
        if (
            fit.fit_score >= apply_threshold
            and not fit.missing_requirements
        )
        else "REVIEW"
    )

    reason = (
        "; ".join(fit.reasons)
        if fit.reasons
        else "no fit reasons"
    )

    evidence_snapshot = (
        {
            "job_id": fit.job_id,
            "fit_score": fit.fit_score,
            "matched_requirements": list(
                fit.matched_requirements
            ),
            "missing_requirements": list(
                fit.missing_requirements
            ),
            "reasons": list(
                fit.reasons
            ),
            "job_title": str(
                job.get("title", "")
            ),
            "company": str(
                job.get("company", "")
            ),
        },
    )

    decision = create_decision(
        job_id=fit.job_id,
        opportunity_name=opportunity_name,
        decision=decision_name,
        score=fit.fit_score,
        reason=reason,
        evidence_snapshot=evidence_snapshot,
    )

    store.save(decision)

    return JobDecisionResult(
        job_id=fit.job_id,
        opportunity_name=opportunity_name,
        fit=fit,
        decision=decision,
    )


def load_job_decision(
    decision_id: str,
    store: DecisionStore | None = None,
) -> DecisionRecord | None:
    if store is None:
        store = DecisionStore()

    return store.get(
        decision_id
    )
