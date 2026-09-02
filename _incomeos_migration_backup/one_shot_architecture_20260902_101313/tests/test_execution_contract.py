from __future__ import annotations

import sqlite3
import subprocess

import pytest

from incomeos.applications import engine as applications_engine
from incomeos.executor import orchestrator
from incomeos.opportunities.engine import IncomeOpportunity, OpportunityMatch
from incomeos.tracking import database as tracking_database
from incomeos.tracking.models import ActionResult, ActionState


@pytest.fixture
def isolated_tracking_db(monkeypatch, tmp_path):
    monkeypatch.setattr(tracking_database, "DB_PATH", tmp_path / "incomeos.db")


def test_planned_action_has_no_execution_or_external_outcome():
    result = orchestrator.plan_action("Example", "example-command")

    assert result.state is ActionState.PLANNED
    assert result.executed_command == ()
    assert not result.externally_submitted
    assert not result.externally_confirmed


def test_placeholder_is_disabled_and_persisted(monkeypatch, tmp_path, isolated_tracking_db):
    opportunity = IncomeOpportunity(
        name="Python Automation",
        description="Test opportunity.",
        required_skills=("Python",),
        skill_weights=(1.0,),
        base_value=0.9,
        difficulty=0.2,
    )
    match = OpportunityMatch(opportunity, 1.0, 0.8, ("Python",), ())
    monkeypatch.setattr(orchestrator, "build_master_profile", lambda _: object())
    monkeypatch.setattr(orchestrator, "match_opportunities", lambda _: (match,))

    result = orchestrator.run_opportunity(tmp_path, force=True)
    persisted = tracking_database.get_recent_execution("Python Automation")

    assert result is not None
    assert result.state is ActionState.DISABLED
    assert not result.externally_submitted
    assert not result.externally_confirmed
    assert persisted is not None
    assert persisted.state is ActionState.DISABLED
    assert persisted.executed_command == ""


def test_successful_local_execution_is_not_submission_or_confirmation(monkeypatch):
    monkeypatch.setattr(
        orchestrator.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0],
            0,
            stdout="ok\n",
            stderr="",
        ),
    )
    result = orchestrator.execute_local_command(
        "local-test",
        ("local-command", "--safe"),
    )

    assert result.state is ActionState.EXECUTED
    assert result.exit_code == 0
    assert result.output_log.strip() == "ok"
    assert not result.externally_submitted
    assert not result.externally_confirmed


def test_failed_local_execution_reports_failed_state(monkeypatch):
    monkeypatch.setattr(
        orchestrator.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0],
            7,
            stdout="",
            stderr="failed",
        ),
    )
    result = orchestrator.execute_local_command(
        "local-test",
        ("local-command", "--fails"),
    )

    assert result.state is ActionState.FAILED
    assert result.exit_code == 7
    assert not result.externally_submitted
    assert not result.externally_confirmed


def test_timed_out_local_execution_reports_failed_state(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(orchestrator.subprocess, "run", timeout)
    result = orchestrator.execute_local_command(
        "local-test",
        ("local-command", "--slow"),
        timeout=0.01,
    )

    assert result.state is ActionState.FAILED
    assert "timed out" in result.error_log
    assert not result.externally_submitted
    assert not result.externally_confirmed


def test_submitted_and_confirmed_states_require_external_evidence():
    with pytest.raises(ValueError):
        ActionResult("test", "command", ActionState.SUBMITTED)

    with pytest.raises(ValueError):
        ActionResult(
            "test",
            "command",
            ActionState.CONFIRMED,
            externally_submitted=True,
        )


def test_application_preparation_stays_pending_and_is_idempotent(monkeypatch, tmp_path):
    job = {
        "id": 42,
        "title": "Python Engineer",
        "url": "https://example.test/jobs/42",
        "company": "Example Co",
    }
    monkeypatch.setattr(
        applications_engine,
        "get_jobs_by_skill",
        lambda *args, **kwargs: [job],
    )

    first = applications_engine.apply_to_jobs(
        "Python",
        open_browser=False,
        data_dir=tmp_path,
    )
    second = applications_engine.apply_to_jobs(
        "Python",
        open_browser=False,
        data_dir=tmp_path,
    )
    conn = sqlite3.connect(tmp_path / "applications.db")
    rows = conn.execute("SELECT status, COUNT(*) FROM applications GROUP BY status").fetchall()
    conn.close()

    assert len(first) == 1
    assert first[0].status == "PENDING"
    assert second == []
    assert rows == [("PENDING", 1)]
