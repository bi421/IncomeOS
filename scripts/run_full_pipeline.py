from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from incomeos.skills.aggregator import build_master_profile, save_master_profile
from incomeos.jobs.runtime.runner import run_pipeline
from incomeos.decision import DecisionEngine
from incomeos.decision.explainer import explain_decision
from incomeos.audit.pipeline_audit import audit_pipeline

def main():
    data_dir = Path("data")
    repos_root = data_dir / "github_repos"

    print("\n" + "=" * 60)
    print("  🚀 INCOMEOS – FULL PIPELINE EXECUTION")
    print("=" * 60)

    # Step 1: Skills
    print("\n📊 1. Building skill profile...")
    try:
        profile = build_master_profile(repos_root)
        save_master_profile(profile, data_dir / "profile" / "master_skill_profile.json")
        print(f"   ✅ Found {len(profile.skills)} unique skills from {profile.repository_count} repositories")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return

    # Step 2: Jobs
    print("\n💼 2. Fetching jobs...")
    try:
        result = run_pipeline(data_dir)
        print(f"   ✅ Fetched: {result.total_fetched}, Validated: {result.total_validated}, Inserted: {result.total_inserted}, Skipped: {result.total_skipped}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return

    # Step 3: Decision
    print("\n🧠 3. Making decision...")
    try:
        decision = DecisionEngine.decide(repos_root, force=True)
        if decision:
            print(explain_decision(decision))
            if decision.is_actionable:
                print(f"\n   ✅ ACTIONABLE! Command to run: {decision.action.command}")
            else:
                print("\n   ⏳ Not actionable.")
        else:
            print("   ❌ No decision")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return

    # Step 4: Audit
    print("\n🔍 4. Running pipeline audit...")
    try:
        report = audit_pipeline(repos_root, data_dir)
        report.print()
    except Exception as e:
        print(f"   ❌ Audit failed: {e}")

    print("\n" + "=" * 60)
    print("  ✅ PIPELINE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
