from __future__ import annotations

import subprocess
from pathlib import Path

from incomeos.decision.persistence import DecisionStore
from incomeos.decision.service import evaluate_and_persist
from incomeos.jobs.fit import JobFit
from incomeos.opportunities.engine import match_opportunities
from incomeos.skills.aggregator import build_master_profile
from incomeos.tracking.database import get_recent_execution, log_finish, log_start
from incomeos.tracking.models import ActionResult, ActionState

ACTION_MAP = {
    "Python Automation": "PREPARE_COVER_LETTER",
    "Data Engineering Support": "PREPARE_COVER_LETTER",
    "C++ Quant / Performance Engineering": "PREPARE_COVER_LETTER",
    "Docker Deployment Support": "PREPARE_COVER_LETTER",
    "Build System Engineering": "PREPARE_COVER_LETTER",
}


def plan_action(action_name: str, command: str) -> ActionResult:
    """Create a local plan without executing or contacting an external service."""
    return ActionResult(
        action_name=action_name,
        requested_command=command,
        state=ActionState.PLANNED,
    )


def execute_local_command(
    action_name: str,
    command: tuple[str, ...],
    timeout: float = 300,
) -> ActionResult:
    """Run an explicitly supplied local command without external submission."""
    requested_command = " ".join(command)
    try:
        completed = subprocess.run(
            command,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        return ActionResult(
            action_name=action_name,
            requested_command=requested_command,
            state=ActionState.FAILED,
            executed_command=command,
            error_log=f"command timed out after {timeout} seconds: {error}",
        )
    except OSError as error:
        return ActionResult(
            action_name=action_name,
            requested_command=requested_command,
            state=ActionState.FAILED,
            executed_command=command,
            error_log=str(error),
        )
    return ActionResult(
        action_name=action_name,
        requested_command=requested_command,
        state=ActionState.EXECUTED if completed.returncode == 0 else ActionState.FAILED,
        executed_command=command,
        exit_code=completed.returncode,
        output_log=completed.stdout,
        error_log=completed.stderr,
    )


def _build_runtime_job_fit(top) -> JobFit:
    """Convert an opportunity match into the shared JobFit contract."""
    return JobFit(
        job_id=f"opportunity:{top.opportunity.name}",
        fit_score=top.readiness,
        matched_requirements=tuple(top.matched_skills),
        missing_requirements=tuple(top.missing_skills),
        reasons=(
            f"readiness={top.readiness:.6f}",
            f"score={top.opportunity_score:.6f}",
            f"matched={','.join(top.matched_skills) or 'none'}",
            f"missing={','.join(top.missing_skills) or 'none'}",
            f"basis={top.readiness_basis}",
        ),
    )


def run_opportunity(
    repos_root: str | Path,
    force: bool = False,
    decision_db_path: str | Path = "data/decisions.db",
) -> ActionResult | None:
    """Persist an opportunity decision and stop at the human-action boundary."""
    root = Path(repos_root)
    profile = build_master_profile(root)
    matches = match_opportunities(profile)
    if not matches:
        return None

    top = matches[0]
    opportunity_name = top.opportunity.name
    plan = ACTION_MAP.get(opportunity_name)
    if plan is None:
        return None

    fit = _build_runtime_job_fit(top)
    store = DecisionStore(decision_db_path)
    decision = evaluate_and_persist(
        fit=fit,
        opportunity_name=opportunity_name,
        apply_threshold=1.0,
        store=store,
    )

    if not force:
        recent = get_recent_execution(opportunity_name, hours=6)
        if recent and recent.state is ActionState.CONFIRMED:
            return None

    log_id = log_start(opportunity_name, plan)
    result = ActionResult(
        action_name=opportunity_name,
        requested_command=plan,
        state=ActionState.DISABLED,
        error_log=(
            f"Decision={decision.record.decision}; "
            "external action requires explicit human confirmation."
        ),
    )
    log_finish(log_id, result)
    return result


def prepare_application_action(
    *,
    action_name: str,
    job_id: str,
) -> ActionResult:
    """Prepare an application action; submission remains outside this function."""
    if not action_name.strip() or not job_id.strip():
        raise ValueError("action_name and job_id are required")
    return plan_action(action_name, f"{action_name}:{job_id}")


if __name__ == "__main__":
    run_opportunity("data/github_repos")
