import sqlite3
from types import SimpleNamespace

from scripts import real_job_pipeline


def test_real_job_pipeline_produces_concrete_decision_output(tmp_path, monkeypatch, capsys):
    jobs_db = tmp_path / "jobs.sqlite3"
    decisions_db = tmp_path / "decisions.sqlite3"
    repos_root = tmp_path / "repos"
    repos_root.mkdir()

    conn = sqlite3.connect(jobs_db)
    try:
        conn.execute(
            """
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                company TEXT,
                url TEXT,
                raw_data TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO jobs (id, title, company, url, raw_data)
            VALUES (1, 'Python Engineer', 'Example Co',
                    'https://example.test/jobs/1',
                    '{"description": "Required skills: Python, Testing"}')
            """
        )
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setattr(
        real_job_pipeline,
        "build_master_profile",
        lambda _: SimpleNamespace(repository_count=1, skills=("Python", "Testing")),
    )

    fake_result = SimpleNamespace(
        fit=SimpleNamespace(
            fit_score=1.0,
            missing_requirements=(),
        ),
        decision=SimpleNamespace(
            decision="APPLY",
            decision_id="decision-1",
        ),
    )
    monkeypatch.setattr(
        real_job_pipeline,
        "persist_job_decision",
        lambda **_: fake_result,
    )

    exit_code = real_job_pipeline.run(
        jobs_db=jobs_db,
        decisions_db=decisions_db,
        repos_root=repos_root,
        limit=10,
        prepare=False,
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "JOBS LOADED: 1" in output
    assert "REQUIRED : Python, Testing" in output
    assert "FIT      : 1.000" in output
    assert "DECISION : APPLY" in output
    assert "DECISION_ID: decision-1" in output
    assert "REAL JOBS READ       : 1" in output
    assert "DECISIONS PERSISTED  : 1" in output
    assert "APPLY CANDIDATES     : 1" in output
    assert "EXTERNAL SUBMISSION  : NOT PERFORMED" in output
