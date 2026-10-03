from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

ROOT = Path(__file__).resolve().parent.parent


def _run(script: str) -> None:
    subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        check=True,
    )


def daily_job() -> None:
    print(f"\n🔄 Running daily pipeline at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        _run("scripts/run_full_pipeline.py")
        _run("scripts/apply_to_jobs.py")
        _run("scripts/apply_browser.py")
    except Exception as exc:
        print(f"❌ Daily job failed: {exc}")
        raise


if __name__ == "__main__":
    print("⏰ Daily Scheduler started. Runs every 24 hours.")
    print("   Press Ctrl+C to stop.")
    scheduler = BlockingScheduler()
    scheduler.add_job(
        daily_job,
        trigger=IntervalTrigger(days=1),
        id="incomeos_daily_pipeline",
        replace_existing=True,
    )
    scheduler.start()
