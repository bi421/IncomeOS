from incomeos.decision.service import (
    evaluate_and_persist,
)
from incomeos.decision.persistence import DecisionStore
from incomeos.jobs.fit import JobFit


def fit(*, score=1.0, missing=()):
    return JobFit(
        job_id="job-100",
        fit_score=score,
        matched_requirements=("Python",),
        missing_requirements=tuple(missing),
        reasons=("Python: level=A; confidence=0.95",),
    )


def test_apply_decision_is_persisted(tmp_path):
    store = DecisionStore(
        tmp_path / "decisions.db"
    )

    result = evaluate_and_persist(
        fit=fit(),
        opportunity_name="Python Automation",
        store=store,
    )

    assert result.persisted
    assert result.record.decision == "APPLY"
    assert result.record.job_id == "job-100"

    loaded = store.get(
        result.record.decision_id
    )

    assert loaded == result.record


def test_missing_requirement_produces_review(tmp_path):
    store = DecisionStore(
        tmp_path / "decisions.db"
    )

    result = evaluate_and_persist(
        fit=fit(
            score=0.5,
            missing=("Testing",),
        ),
        opportunity_name="Python Automation",
        store=store,
    )

    assert result.record.decision == "REVIEW"
