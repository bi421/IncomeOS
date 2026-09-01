from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import sqlite3
from typing import Any

from incomeos.skills.aggregator import build_master_profile
from incomeos.opportunities.engine import match_opportunities
from incomeos.jobs.integration import count_jobs_by_skills

@dataclass
class AuditItem:
    status: str  # "PASS", "WARN", "FAIL"
    category: str
    description: str
    details: dict[str, Any] = field(default_factory=dict)

@dataclass
class PipelineAuditReport:
    items: list[AuditItem] = field(default_factory=list)

    def add_pass(self, category: str, desc: str, details: dict = None):
        self.items.append(AuditItem("PASS", category, desc, details or {}))

    def add_warn(self, category: str, desc: str, details: dict = None):
        self.items.append(AuditItem("WARN", category, desc, details or {}))

    def add_fail(self, category: str, desc: str, details: dict = None):
        self.items.append(AuditItem("FAIL", category, desc, details or {}))

    def print(self):
        print("\n" + "=" * 60)
        print("  🔍 PIPELINE AUDIT REPORT")
        print("=" * 60)
        for item in self.items:
            emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(item.status, "❓")
            print(f"{emoji} [{item.status}] {item.category}: {item.description}")
            if item.details:
                for k, v in item.details.items():
                    print(f"      {k}: {v}")
        print("=" * 60)

def audit_pipeline(repos_root: str | Path, data_dir: Path = Path("data")) -> PipelineAuditReport:
    report = PipelineAuditReport()
    root = Path(repos_root)

    # 1. SKILLS AUDIT
    try:
        profile = build_master_profile(root)
        report.add_pass("Skills", f"Loaded {len(profile.skills)} unique skills from {profile.repository_count} repos")
        for skill in profile.skills[:5]:  # top 5
            report.add_pass("Skills", f"Skill '{skill.name}' confidence={skill.confidence:.2f}, evidence={skill.evidence_count}", {"confidence": skill.confidence, "evidence": skill.evidence_count})
    except Exception as e:
        report.add_fail("Skills", f"Failed to build profile: {e}")

    # 2. OPPORTUNITIES AUDIT
    try:
        profile = build_master_profile(root)
        matches = match_opportunities(profile)
        if matches:
            top = matches[0]
            report.add_pass("Opportunities", f"Top opportunity: {top.opportunity.name} (score={top.opportunity_score:.3f})", 
                            {"name": top.opportunity.name, "score": top.opportunity_score, "readiness": top.readiness})
            if top.opportunity_score > 0.7:
                report.add_pass("Opportunities", "Score > 0.7 → HIGH confidence", {"threshold": "0.7"})
            elif top.opportunity_score > 0.4:
                report.add_warn("Opportunities", "Score between 0.4 and 0.7 → MEDIUM confidence")
            else:
                report.add_warn("Opportunities", "Score < 0.4 → LOW confidence")
        else:
            report.add_fail("Opportunities", "No opportunities found")
    except Exception as e:
        report.add_fail("Opportunities", f"Failed: {e}")

    # 3. JOBS DB AUDIT
    db_path = data_dir / "jobs" / "incomeos_jobs.sqlite3"
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.execute("SELECT COUNT(*) FROM jobs")
            total = cur.fetchone()[0]
            cur = conn.execute("SELECT COUNT(DISTINCT url) FROM jobs")
            unique_urls = cur.fetchone()[0]
            conn.close()
            report.add_pass("Jobs DB", f"Found {total} job records, {unique_urls} unique URLs", {"total": total, "unique": unique_urls})
            if unique_urls == total:
                report.add_pass("Jobs DB", "No duplicate URLs (deduplication working)")
            else:
                report.add_warn("Jobs DB", f"{total - unique_urls} duplicate rows found")
        except Exception as e:
            report.add_fail("Jobs DB", f"Failed to read DB: {e}")
    else:
        report.add_fail("Jobs DB", "Database file not found")

    # 4. JOBS vs SKILLS AUDIT (Validation)
    try:
        profile = build_master_profile(root)
        matches = match_opportunities(profile)
        if matches:
            top = matches[0]
            required = list(top.opportunity.required_skills)
            counts = count_jobs_by_skills(required, db_path)
            total_jobs = sum(counts.values())
            if total_jobs > 0:
                report.add_pass("Job-Skill Match", f"Found {total_jobs} jobs matching skills: {', '.join(required)}", counts)
            else:
                report.add_warn("Job-Skill Match", f"No jobs found for skills: {', '.join(required)}")
    except Exception as e:
        report.add_fail("Job-Skill Match", f"Failed: {e}")

    # 5. DECISION AUDIT (Final verdict)
    try:
        from incomeos.decision import DecisionEngine
        decision = DecisionEngine.decide(root, force=True)
        if decision:
            report.add_pass("Decision", f"Decision: {decision.opportunity_name} | Actionable: {decision.is_actionable} | Severity: {decision.decision_severity.value}")
            if decision.is_actionable:
                report.add_pass("Decision", f"Action command: {decision.action.command}")
            else:
                report.add_warn("Decision", "Decision is not actionable (score too low or recent success)")
        else:
            report.add_fail("Decision", "No decision could be made")
    except Exception as e:
        report.add_fail("Decision", f"Failed: {e}")

    return report
