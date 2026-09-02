from __future__ import annotations

import subprocess
from pathlib import Path

from incomeos.skills.aggregator import build_master_profile
from incomeos.opportunities.engine import match_opportunities
from incomeos.tracking.database import log_start, log_finish, get_recent_execution
from incomeos.tracking.models import ActionResult, ActionState
from incomeos.decision.persistence import DecisionStore
from incomeos.decision.service import evaluate_and_persist
from incomeos.jobs.fit import JobFit


ACTION_MAP = {
    "Python Automation": "python -c 'print(\"Python Automation executed\")'",
    "Data Engineering Support": "python -c 'print(\"Data Engineering executed\")'",
    "C++ Quant / Performance Engineering": "python -c 'print(\"C++ Quant executed\")'",
    "Docker Deployment Support": "docker --version",
    "Build System Engineering": "cmake --version",
}


def plan_action(
    action_name: str,
    command: str,
) -> ActionResult:
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
    """Run a controlled local command without claiming external completion."""

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
            error_log=(
                f"command timed out after {timeout} seconds: {error}"
            ),
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
        state=(
            ActionState.EXECUTED
            if completed.returncode == 0
            else ActionState.FAILED
        ),
        executed_command=command,
        exit_code=completed.returncode,
        output_log=completed.stdout,
        error_log=completed.stderr,
    )


def _build_runtime_job_fit(top) -> JobFit:
    """
    Convert the live opportunity result into the common JobFit contract.

    The current runtime operates at opportunity level, not at a concrete
    external job record. Therefore the identifier is explicitly namespaced
    as an opportunity decision and is never presented as a submitted job.
    """

    opportunity_id = f"opportunity:{top.opportunity.name}"

    reasons = (
        f"readiness={top.readiness:.6f}",
        f"score={top.opportunity_score:.6f}",
        f"matched={','.join(top.matched_skills) or 'none'}",
        f"missing={','.join(top.missing_skills) or 'none'}",
        f"basis={top.readiness_basis}",
    )

    return JobFit(
        job_id=opportunity_id,
        fit_score=top.readiness,
        matched_requirements=tuple(top.matched_skills),
        missing_requirements=tuple(top.missing_skills),
        reasons=reasons,
    )


def run_opportunity(
    repos_root: str | Path,
    force: bool = False,
    decision_db_path: str | Path = "data/decisions.db",
) -> ActionResult | None:
    """
    Live IncomeOS runtime path.

    Flow:

        evidence
          -> skill confidence
          -> capability
          -> opportunity match
          -> persistent decision
          -> execution boundary

    External submission is never claimed here.
    """

    root = Path(repos_root)

    profile = build_master_profile(root)
    matches = match_opportunities(profile)

    if not matches:
        print("No opportunities found.")
        return None

    top = matches[0]
    opp_name = top.opportunity.name
    command = ACTION_MAP.get(opp_name)

    if not command:
        print(
            f"No action defined for {opp_name}"
        )
        return None

    fit = _build_runtime_job_fit(top)

    decision_store = DecisionStore(
        decision_db_path
    )

    decision_result = evaluate_and_persist(
        fit=fit,
        opportunity_name=opp_name,
        apply_threshold=1.0,
        store=decision_store,
    )

    print(
        "Decision persisted: "
        f"{decision_result.record.decision_id} | "
        f"{decision_result.record.decision} | "
        f"score={decision_result.record.score:.3f}"
    )

    if not force:
        recent = get_recent_execution(
            opp_name,
            hours=6,
        )

        if (
            recent
            and recent.state is ActionState.CONFIRMED
        ):
            print(
                f"{opp_name} already succeeded recently. Skipping."
            )
            return None

    print(
        f"Preparing: {opp_name} "
        f"(score={top.opportunity_score:.3f})"
    )

    log_id = log_start(
        opp_name,
        command,
    )

    result = ActionResult(
        action_name=opp_name,
        requested_command=command,
        state=ActionState.DISABLED,
        error_log=(
            "IncomeOS has no real action implementation "
            "for this opportunity."
        ),
    )

    log_finish(
        log_id,
        result,
    )

    print(
        "Disabled: no real business action was executed."
    )

    return result


if __name__ == "__main__":
    run_opportunity(
        "data/github_repos"
    )
