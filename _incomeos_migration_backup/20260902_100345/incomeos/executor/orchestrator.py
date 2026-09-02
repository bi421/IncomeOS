from __future__ import annotations
import subprocess
from pathlib import Path

from incomeos.skills.aggregator import build_master_profile
from incomeos.opportunities.engine import match_opportunities
from incomeos.tracking.database import log_start, log_finish, get_recent_execution
from incomeos.tracking.models import ActionResult, ActionState

ACTION_MAP = {
    "Python Automation": "python -c 'print(\"Python Automation executed\")'",
    "Data Engineering Support": "python -c 'print(\"Data Engineering executed\")'",
    "C++ Quant / Performance Engineering": "python -c 'print(\"C++ Quant executed\")'",
    "Docker Deployment Support": "docker --version",
    "Build System Engineering": "cmake --version",
}

def plan_action(action_name: str, command: str) -> ActionResult:
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


def run_opportunity(repos_root: str | Path, force: bool = False) -> ActionResult | None:
    root = Path(repos_root)
    profile = build_master_profile(root)
    matches = match_opportunities(profile)
    if not matches:
        print("No opportunities found.")
        return

    top = matches[0]
    opp_name = top.opportunity.name
    command = ACTION_MAP.get(opp_name)

    if not command:
        print(f"âš ï¸ No action defined for {opp_name}")
        return

    if not force:
        recent = get_recent_execution(opp_name, hours=6)
        if recent and recent.state is ActionState.CONFIRMED:
            print(f"â³ {opp_name} already succeeded recently. Skipping.")
            return

    print(f"â–¶ï¸ Preparing: {opp_name} (score={top.opportunity_score:.3f})")
    log_id = log_start(opp_name, command)
    result = ActionResult(
        action_name=opp_name,
        requested_command=command,
        state=ActionState.DISABLED,
        error_log="IncomeOS has no real action implementation for this opportunity.",
    )
    log_finish(log_id, result)
    print("â„¹ï¸ Disabled: no real business action was executed.")
    return result

if __name__ == "__main__":
    run_opportunity("data/github_repos")
