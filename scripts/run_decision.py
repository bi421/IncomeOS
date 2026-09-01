from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from incomeos.decision import DecisionEngine
from incomeos.decision.explainer import explain_decision

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    decision = DecisionEngine.decide("data/github_repos", force=args.force)
    if decision:
        print(explain_decision(decision))
        if decision.is_actionable:
            print("\n✅ Actionable. Run:")
            print(f"  {decision.action.command}")
        else:
            print("\n⏳ Not actionable. Try --force to override 6h cooldown.")
    else:
        print("❌ No decision.")
