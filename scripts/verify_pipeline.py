"""
Pipeline Verification Test
--------------------------
Checks if the IncomeOS pipeline actually produces real outputs.
Run this to verify the system is fully operational.
"""

import sys
import json
import sqlite3
from pathlib import Path

def check_file_exists(p: Path) -> bool:
    return p.exists() and p.stat().st_size > 0

def main():
    errors = []
    warnings = []
    successes = []

    base = Path("data")
    profile_path = base / "profile" / "master_skill_profile.json"
    jobs_db_path = base / "jobs" / "incomeos_jobs.sqlite3"
    repos_path = base / "github_repos"

    print("\n" + "=" * 60)
    print("  🔍 AUDIT TEST: PIPELINE OUTPUT VERIFICATION")
    print("=" * 60)

    # 1. Profile
    if check_file_exists(profile_path):
        try:
            with open(profile_path, encoding="utf-8") as f:
                data = json.load(f)
            skills = data.get("skills", [])
            if skills:
                successes.append(f"✅ Profile: {len(skills)} skills found (confidence top: {skills[0].get('name', 'N/A')})")
            else:
                errors.append("❌ Profile: No skills found in JSON")
        except Exception as e:
            errors.append(f"❌ Profile: JSON read error - {e}")
    else:
        errors.append(f"❌ Profile: File missing ({profile_path})")

    # 2. Jobs DB
    if check_file_exists(jobs_db_path):
        try:
            conn = sqlite3.connect(str(jobs_db_path))
            count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            sources = conn.execute("SELECT source, COUNT(*) FROM jobs GROUP BY source").fetchall()
            conn.close()
            if count > 0:
                src_str = ", ".join([f"{s}={c}" for s, c in sources])
                successes.append(f"✅ Jobs DB: {count} records ({src_str})")
            else:
                errors.append("❌ Jobs DB: 0 records found")
        except Exception as e:
            errors.append(f"❌ Jobs DB: Read error - {e}")
    else:
        errors.append(f"❌ Jobs DB: File missing ({jobs_db_path})")

    # 3. Decision Engine
    try:
        sys.path.insert(0, str(Path.cwd()))
        from incomeos.decision import DecisionEngine
        decision = DecisionEngine.decide(repos_path, force=True)
        if decision:
            if decision.is_actionable:
                successes.append(f"✅ Decision: Actionable -> {decision.opportunity_name} (score={decision.opportunity_score:.3f})")
            else:
                warnings.append(f"⚠️ Decision: Not actionable -> {decision.opportunity_name} (score={decision.opportunity_score:.3f})")
        else:
            errors.append("❌ Decision: No decision generated")
    except Exception as e:
        errors.append(f"❌ Decision: Failed - {e}")

    # 4. Audit Engine (quick check)
    try:
        from incomeos.audit.pipeline_audit import audit_pipeline
        report = audit_pipeline(repos_path)
        passes = sum(1 for i in report.items if i.status == "PASS")
        fails = sum(1 for i in report.items if i.status == "FAIL")
        if fails == 0 and passes > 0:
            successes.append(f"✅ Audit: {passes} checks PASS, 0 FAIL")
        else:
            errors.append(f"❌ Audit: {fails} FAIL checks found")
    except Exception as e:
        errors.append(f"❌ Audit: Failed - {e}")

    # 5. Final summary
    print("\n" + "-" * 60)
    print("  RESULTS")
    print("-" * 60)
    for s in successes:
        print(f"  {s}")
    for w in warnings:
        print(f"  {w}")
    for e in errors:
        print(f"  {e}")
    print("-" * 60)

    if not errors:
        print("\n✅ VERDICT: PASS — Pipeline produces real outputs and passes audit.")
        sys.exit(0)
    else:
        print(f"\n❌ VERDICT: FAIL — {len(errors)} error(s) detected. Please run `python scripts/run_full_pipeline.py` first.")
        sys.exit(1)

if __name__ == "__main__":
    main()
