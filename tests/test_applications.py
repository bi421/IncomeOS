from __future__ import annotations

import json
from pathlib import Path

import pytest

from incomeos.applications.generator import EvidenceBoundGenerator


def _profile(tmp_path: Path) -> Path:
    path = tmp_path / "master_skill_profile.json"
    path.write_text(
        json.dumps(
            {
                "skills": [{"name": "Python", "confidence": 1.0}],
                "verified_evidence": [
                    {
                        "id": "tests-168",
                        "claim": "168 passing tests were documented.",
                        "source": "README.md",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_prompt_contains_only_explicit_evidence(tmp_path: Path) -> None:
    generator = EvidenceBoundGenerator(_profile(tmp_path))
    prompt = generator.build_prompt("Python automation engineer")
    assert "tests-168" in prompt
    assert "Never invent" in prompt


def test_deterministic_generation_is_grounded(tmp_path: Path) -> None:
    generator = EvidenceBoundGenerator(_profile(tmp_path))
    result = generator.generate("Python automation engineer")
    assert "168 passing tests" in result.cover_letter
    assert result.claim_ids == ("tests-168",)


def test_llm_unknown_claim_id_fails_closed(tmp_path: Path) -> None:
    generator = EvidenceBoundGenerator(_profile(tmp_path))

    def fake_llm(_: str) -> str:
        return json.dumps(
            {
                "claim_ids": ["invented"],
                "cover_letter": "I built everything.",
                "resume_summary": "Expert engineer.",
            }
        )

    with pytest.raises(ValueError, match="unsupported"):
        generator.generate("Python role", llm=fake_llm)


def test_llm_malformed_output_fails_closed(tmp_path: Path) -> None:
    generator = EvidenceBoundGenerator(_profile(tmp_path))
    with pytest.raises(ValueError, match="valid JSON"):
        generator.generate("Python role", llm=lambda _: "not-json")
