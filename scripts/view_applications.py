import sqlite3
from pathlib import Path

def view_applications():
    db_path = Path("data") / "applications.db"
    if not db_path.exists():
        print("❌ No applications yet.")
        return
    conn = sqlite3.connect(str(db_path))
    cur = conn.execute("SELECT job_title, company, status, applied_at FROM applications ORDER BY applied_at DESC LIMIT 20")
    rows = cur.fetchall()
    conn.close()
    if rows:
        print("\n📋 Recent Applications:")
        print("-" * 80)
        print(f"{'Job Title':<30} {'Company':<20} {'Status':<10} {'Applied At':<20}")
        print("-" * 80)
        for row in rows:
            print(f"{row[0][:28]:<30} {row[1][:18]:<20} {row[2]:<10} {row[3][:16]:<20}")
        print("-" * 80)
    else:
        print("No applications found.")

if __name__ == "__main__":
    view_applications()
