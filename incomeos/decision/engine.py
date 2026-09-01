from __future__ import annotations
from pathlib import Path
from typing import Optional

from incomeos.skills.aggregator import build_master_profile
from incomeos.opportunities.engine import match_opportunities
from incomeos.tracking.database import get_recent_execution
from incomeos.jobs.integration import count_jobs_by_skills
from .models import Decision, DecisionReason, ActionPlan, DecisionSeverity

ACTION_MAP = {
    "Python Automation": ("python -c 'print(\"Python Automation executed\")'", 5),
    "Data Engineering Support": ("python -c 'print(\"Data Engineering executed\")'", 10),
    "C++ Quant / Performance Engineering": ("python -c 'print(\"C++ Quant executed\")'", 30),
    "Docker Deployment Support": ("docker --version", 2),
    "Build System Engineering": ("cmake --version", 3),
}

def make_decision(repos_root: str | Path, force: bool = False, data_dir: Path = Path("data")) -> Optional[Decision]:
    root = Path(repos_root)
    profile = build_master_profile(root)
    matches = match_opportunities(profile)
    if not matches:
        return None

    top = matches[0]
    opp = top.opportunity
    opp_name = opp.name
    command, duration = ACTION_MAP.get(opp_name, (None, 0))
    if not command:
        return None

    required_skills = list(opp.required_skills)
    db_path = data_dir / "jobs" / "incomeos_jobs.sqlite3"
    job_counts = count_jobs_by_skills(required_skills, db_path)
    total_jobs = sum(job_counts.values())
    job_evidence = DecisionReason(
        text=f"Found {total_jobs} job listings matching skills: {', '.join(required_skills)}",
        confidence=min(1.0, total_jobs / 10.0)
    )

    recent = get_recent_execution(opp_name, hours=6)
    skip_due_to_recent = (recent is not None and recent.status == "success" and not force)

    reasons = [
        DecisionReason(f"Skill readiness = {top.readiness:.3f}", confidence=top.readiness),
        DecisionReason(f"Opportunity score = {top.opportunity_score:.3f}", confidence=top.opportunity_score),
        DecisionReason(f"Matched skills: {', '.join(top.matched_skills)}", confidence=1.0),
        job_evidence,
    ]
    if top.missing_skills:
        reasons.append(DecisionReason(f"Missing skills: {', '.join(top.missing_skills)}", confidence=0.5))
    if skip_due_to_recent:
        reasons.append(DecisionReason("Skipping: recent success within 6h (use --force to override)", confidence=1.0))

    is_actionable = (top.opportunity_score > 0.4 and not skip_due_to_recent)
    severity = DecisionSeverity.HIGH if top.opportunity_score > 0.7 else DecisionSeverity.MEDIUM

    action = ActionPlan(opp_name, command, duration, severity)
    explanation = f"Decision based on {len(reasons)} evidence points: " + "; ".join(r.text for r in reasons)

    return Decision(
        opportunity_name=opp_name,
        opportunity_score=top.opportunity_score,
        readiness=top.readiness,
        reasons=tuple(reasons),
        action=action,
        decision_severity=severity,
        is_actionable=is_actionable,
        explanation=explanation
    )

class DecisionEngine:
    @staticmethod
    def decide(repos_root: str | Path, force: bool = False) -> Optional[Decision]:
        return make_decision(repos_root, force)
