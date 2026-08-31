from __future__ import annotations
import time
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .orchestrator import run_opportunity

def job():
    print(f"\nðŸ”„ Scheduled run at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    run_opportunity("data/github_repos", force=False)

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(job, trigger=IntervalTrigger(hours=1))
    print("â° Scheduler started. Runs every hour.")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("ðŸ›‘ Scheduler stopped.")
