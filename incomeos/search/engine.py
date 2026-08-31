from __future__ import annotations

from pathlib import Path
from typing import Iterable

from incomeos.search.models import SearchDocument, SearchResult


IGNORED_DIRECTORIES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}


EXTENSIONS = {
    ".py": "Python",
    ".pyi": "Python",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".h": "C++",
    ".hpp": "C++",
    ".cmake": "CMake",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".sql": "SQL",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
}


SPECIAL_FILES = {
    "Dockerfile": "Docker",
    "CMakeLists.txt": "CMake",
}


def _category(path: Path) -> str:
    name = path.name

    if name in SPECIAL_FILES:
        return SPECIAL_FILES[name]

    if "test" in name.lower():
        return "Testing"

    return EXTENSIONS.get(path.suffix.lower(), "Other")


def _language(path: Path) -> str:
    name = path.name

    if name in SPECIAL_FILES:
        return SPECIAL_FILES[name]

    return EXTENSIONS.get(path.suffix.lower(), "Unknown")


def index_repository(repository_path: str | Path) -> tuple[SearchDocument, ...]:
    root = Path(repository_path)

    if not root.exists():
        raise FileNotFoundError(root)

    documents: list[SearchDocument] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if any(part in IGNORED_DIRECTORIES for part in path.parts):
            continue

        if path.name not in SPECIAL_FILES and path.suffix.lower() not in EXTENSIONS:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        documents.append(
            SearchDocument(
                repository=root.name,
                path=str(path.relative_to(root)),
                language=_language(path),
                category=_category(path),
                content=content,
            )
        )

    return tuple(sorted(documents, key=lambda x: x.path.lower()))


def index_repositories(root: str | Path) -> tuple[SearchDocument, ...]:
    base = Path(root)

    documents: list[SearchDocument] = []

    for repository in sorted(base.iterdir()):
        if not repository.is_dir():
            continue

        if not (repository / ".git").exists():
            continue

        documents.extend(index_repository(repository))

    return tuple(documents)


def search_documents(
    documents: Iterable[SearchDocument],
    query: str,
    *,
    limit: int = 20,
) -> tuple[SearchResult, ...]:
    terms = tuple(
        term.strip().lower()
        for term in query.split()
        if term.strip()
    )

    if not terms:
        return ()

    results: list[SearchResult] = []

    for document in documents:
        haystack = document.content.lower()
        path_text = document.path.lower()

        matched = tuple(
            term
            for term in terms
            if term in haystack or term in path_text
        )

        if not matched:
            continue

        score = len(matched) / len(terms)

        results.append(
            SearchResult(
                repository=document.repository,
                path=document.path,
                language=document.language,
                category=document.category,
                score=round(score, 6),
                matched_terms=matched,
            )
        )

    results.sort(
        key=lambda item: (
            item.score,
            len(item.matched_terms),
            item.repository,
            item.path,
        ),
        reverse=True,
    )

    return tuple(results[:limit])
