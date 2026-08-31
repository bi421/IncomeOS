from __future__ import annotations
import subprocess
import sys
from pathlib import Path
from datetime import datetime

from incomeos.skills.aggregator import build_master_profile
from incomeos.opportunities.engine import match_opportunities
from incomeos.tracking.database import log_start, log_finish, get_recent_execution

ACTION_MAP = {
    "Python Automation": "python -c 'print(\"Python Automation executed\")'",
    "Data Engineering Support": "python -c 'print(\"Data Engineering executed\")'",
    "C++ Quant / Performance Engineering": "python -c 'print(\"C++ Quant executed\")'",
    "Docker Deployment Support": "docker --version",
    "Build System Engineering": "cmake --version",
}

def run_opportunity(repos_root: str | Path, force: bool = False):
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
        if recent and recent.status == "success":
            print(f"â³ {opp_name} already succeeded recently. Skipping.")
            return

    print(f"â–¶ï¸ Executing: {opp_name} (score={top.opportunity_score:.3f})")
    log_id = log_start(opp_name, command)

    try:
        result = subprocess.run(command.split(), shell=False, capture_output=True, text=True, timeout=300)
        status = "success" if result.returncode == 0 else "failed"
        log_finish(log_id, status, result.returncode, result.stdout, result.stderr)
        print(f"âœ… Done. Status: {status}")
    except Exception as e:
        log_finish(log_id, "failed", -1, "", str(e))
        print(f"âŒ Failed: {e}")

if __name__ == "__main__":
    run_opportunity("data/github_repos")
