import re
from pathlib import Path


_SECRET_PATTERNS = (
    re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{20,}\b"),
)

_SOURCE_SUFFIXES = {".py", ".ps1", ".txt", ".md", ".yml", ".yaml", ".toml", ".ini", ".cfg"}


def test_repository_contains_no_embedded_telegram_bot_tokens() -> None:
    root = Path(__file__).resolve().parents[1]

    offenders: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _SOURCE_SUFFIXES:
            continue
        if any(part in {".git", ".venv", "venv", "__pycache__"} for part in path.parts):
            continue

        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            continue

        if any(pattern.search(text) for pattern in _SECRET_PATTERNS):
            offenders.append(str(path.relative_to(root)))

    assert offenders == [], f"embedded credential pattern found in: {offenders}"
