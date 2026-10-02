from __future__ import annotations

from scripts.incomeos_dry_run import run


def test_complete_end_to_end_dry_run(capsys):
    run()
    output = capsys.readouterr().out
    assert "INCOMEOS END-TO-END DRY RUN" in output
    assert "JOB FIT       : PASS" in output
    assert "DECISION      : PASS" in output
    assert "OUTCOME       : PASS" in output
    assert "FEEDBACK      : PASS" in output
    assert "VERIFICATION  : PASS" in output
    assert "DRY RUN RESULT: PASS" in output
