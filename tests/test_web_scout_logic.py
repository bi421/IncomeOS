from __future__ import annotations

import sqlite3
from types import SimpleNamespace

import incomeos.search.web_scout as scout


def _db_factory(path):
    def get_db():
        return sqlite3.connect(path)
    return get_db


def test_web_scout_applies_global_limit_and_url_dedup(tmp_path, monkeypatch):
    db_path = tmp_path / "web.db"
    monkeypatch.setattr(scout, "get_db", _db_factory(db_path))
    monkeypatch.setattr(
        scout,
        "build_master_profile",
        lambda _: SimpleNamespace(
            skills=(
                SimpleNamespace(name="Python", confidence=0.9),
                SimpleNamespace(name="Docker", confidence=0.8),
            )
        ),
    )

    calls = []

    def source_one(skills):
        calls.append("one")
        return [
            {
                "title": "A",
                "url": "https://EXAMPLE.com/a#fragment",
                "snippet": "A",
                "matched_skills": skills,
                "source": "one",
                "found_at": "now",
            },
            {
                "title": "B",
                "url": "https://example.com/b",
                "snippet": "B",
                "matched_skills": skills,
                "source": "one",
                "found_at": "now",
            },
        ], None

    def source_two(skills):
        calls.append("two")
        return [
            {
                "title": "A duplicate",
                "url": "https://example.com/a",
                "snippet": "duplicate",
                "matched_skills": skills,
                "source": "two",
                "found_at": "now",
            },
            {
                "title": "C",
                "url": "https://example.com/c",
                "snippet": "C",
                "matched_skills": skills,
                "source": "two",
                "found_at": "now",
            },
        ], None

    def source_three(skills):
        calls.append("three")
        return [
            {
                "title": "D",
                "url": "https://example.com/d",
                "snippet": "D",
                "matched_skills": skills,
                "source": "three",
                "found_at": "now",
            }
        ], None

    monkeypatch.setattr(scout, "_search_remotive_api", source_one)
    monkeypatch.setattr(scout, "_search_arbeitnow_api", source_two)
    monkeypatch.setattr(scout, "_search_rss_feeds", source_three)

    result = scout.search_opportunities(str(tmp_path), max_results=2)

    assert calls == ["one", "two", "three"]
    assert len(result) == 2
    assert [item["url"] for item in result] == [
        "https://example.com/a",
        "https://example.com/b",
    ]

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT url FROM web_opportunities ORDER BY id"
        ).fetchall()
    assert [row[0] for row in rows] == [
        "https://example.com/a",
        "https://example.com/b",
    ]


def test_web_scout_rejects_non_positive_limit(tmp_path):
    try:
        scout.search_opportunities(str(tmp_path), max_results=0)
    except ValueError as exc:
        assert "max_results" in str(exc)
    else:
        raise AssertionError("non-positive max_results was accepted")
