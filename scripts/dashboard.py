from __future__ import annotations
import sqlite3
import json
from pathlib import Path
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>IncomeOS Dashboard</title>
<style>
body { font-family: Arial; margin: 20px; background: #f4f4f4; }
h1 { color: #2c3e50; }
.card { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
th { background: #3498db; color: white; }
.status-PENDING { color: orange; }
.status-SUBMITTED { color: green; }
.status-FAILED { color: red; }
</style>
</head>
<body>
<h1>📊 IncomeOS Dashboard</h1>
<div class="card">
    <h2>📈 Summary</h2>
    <p>Total Applications: {{ total }}</p>
    <p>Pending: {{ pending }} | Submitted: {{ submitted }} | Failed: {{ failed }}</p>
</div>
<div class="card">
    <h2>📋 Recent Applications</h2>
    <table>
        <tr><th>Job</th><th>Company</th><th>Status</th><th>Applied At</th></tr>
        {% for app in apps %}
        <tr>
            <td>{{ app.job_title }}</td>
            <td>{{ app.company }}</td>
            <td class="status-{{ app.status }}">{{ app.status }}</td>
            <td>{{ app.applied_at[:16] }}</td>
        </tr>
        {% endfor %}
    </table>
</div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    db_path = Path("data") / "applications.db"
    apps = []
    total = pending = submitted = failed = 0
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM applications ORDER BY applied_at DESC LIMIT 50")
        for row in cur.fetchall():
            apps.append(dict(row))
        cur = conn.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
        for row in cur.fetchall():
            if row[0] == "PENDING": pending = row[1]
            elif row[0] == "SUBMITTED": submitted = row[1]
            elif row[0] == "FAILED": failed = row[1]
        total = len(apps)
        conn.close()
    return render_template_string(HTML_TEMPLATE, apps=apps, total=total, pending=pending, submitted=submitted, failed=failed)

@app.route("/api/applications")
def api_applications():
    db_path = Path("data") / "applications.db"
    apps = []
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM applications ORDER BY applied_at DESC")
        for row in cur.fetchall():
            apps.append(dict(row))
        conn.close()
    return jsonify(apps)

def main():
    print("🌐 Starting Dashboard on http://127.0.0.1:5000")
    app.run(debug=False, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
