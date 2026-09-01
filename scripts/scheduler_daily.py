from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
import subprocess
import time

def daily_job():
    print(f"\n🔄 Running daily pipeline at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        subprocess.run(["python", "scripts/run_full_pipeline.py"], check=True)
        subprocess.run(["python", "scripts/apply_to_jobs.py"], check=True)
        subprocess.run(["python", "scripts/apply_browser.py"], check=True)  # хөтөч нээх
    except Exception as e:
        print(f"❌ Daily job failed: {e}")

if __name__ == "__main__":
    print("⏰ Daily Scheduler started. Runs every 24 hours.")
    print("   Press Ctrl+C to stop.")
    scheduler = BlockingScheduler()
    scheduler.add_job(daily_job, trigger=IntervalTrigger(days=1))
    scheduler.start()
