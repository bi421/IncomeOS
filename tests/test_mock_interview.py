import json
from pathlib import Path

from scripts.mock_interview import build_interview, extract_requirements, load_profile


def profile(tmp_path: Path) -> dict:
    path = tmp_path / "profile.json"
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
    return load_profile(path)


def test_extract_requirements_is_deterministic():
    assert extract_requirements("Python and Docker role") == ("Python", "Docker")


def test_star_answer_uses_only_documented_evidence(tmp_path):
    items = build_interview(
        "Python engineer",
        profile(tmp_path),
        count=1,
    )
    assert len(items) == 1
    assert items[0].evidence_ids == ("tests-168",)
    assert "168 passing tests" in items[0].answer
    assert "No additional result is inferred" in items[0].answer


def test_empty_job_description_fails(tmp_path):
    try:
        build_interview("", profile(tmp_path))
    except ValueError:
        pass
    else:
        raise AssertionError("empty job description was accepted")
