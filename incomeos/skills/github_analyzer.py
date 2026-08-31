from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import EvidenceDimension


@dataclass(frozen=True)
class RepositoryEvidence:
    repository: str
    evidence_type: str
    source: str
    detail: str
    dimension: EvidenceDimension = EvidenceDimension.PRESENCE


IGNORED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "pytest_temp",
    ".hypothesis",
}


def analyze_repository(
    repository_path: str | Path,
) -> tuple[RepositoryEvidence, ...]:
    root = Path(repository_path)

    if not root.exists():
        raise FileNotFoundError(root)

    if not root.is_dir():
        raise NotADirectoryError(root)

    evidence: list[RepositoryEvidence] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        if _is_ignored(path, root):
            continue

        relative = path.relative_to(root)
        source = str(relative)

        if path.name == "pyproject.toml":
            evidence.append(
                RepositoryEvidence(
                    repository=root.name,
                    evidence_type="configuration",
                    source=source,
                    detail="Python project configuration detected.",
                    dimension=EvidenceDimension.PRESENCE,
                )
            )

        elif path.name == "requirements.txt":
            evidence.append(
                RepositoryEvidence(
                    repository=root.name,
                    evidence_type="dependency",
                    source=source,
                    detail="Python dependency manifest detected.",
                    dimension=EvidenceDimension.PRESENCE,
                )
            )

        elif path.suffix == ".py":
            evidence.append(
                RepositoryEvidence(
                    repository=root.name,
                    evidence_type="direct_code",
                    source=source,
                    detail="Python source file detected.",
                    dimension=EvidenceDimension.IMPLEMENTATION,
                )
            )

        elif path.suffix in {
            ".cpp",
            ".cc",
            ".cxx",
            ".h",
            ".hpp",
        }:
            evidence.append(
                RepositoryEvidence(
                    repository=root.name,
                    evidence_type="direct_code",
                    source=source,
                    detail="C/C++ source or header detected.",
                    dimension=EvidenceDimension.IMPLEMENTATION,
                )
            )

        elif path.name == "CMakeLists.txt":
            evidence.append(
                RepositoryEvidence(
                    repository=root.name,
                    evidence_type="build_system",
                    source=source,
                    detail="CMake build configuration detected.",
                    dimension=EvidenceDimension.ENGINEERING,
                )
            )

        elif (
            "test" in path.name.lower()
            or any(
                part.lower() in {"tests", "__tests__"}
                for part in path.parts
            )
        ):
            evidence.append(
                RepositoryEvidence(
                    repository=root.name,
                    evidence_type="test",
                    source=source,
                    detail="Test-related file detected.",
                    dimension=EvidenceDimension.VALIDATION,
                )
            )

        elif path.name == "Dockerfile":
            evidence.append(
                RepositoryEvidence(
                    repository=root.name,
                    evidence_type="deployment",
                    source=source,
                    detail="Docker deployment configuration detected.",
                    dimension=EvidenceDimension.ENGINEERING,
                )
            )

    return tuple(evidence)


def _is_ignored(
    path: Path,
    root: Path,
) -> bool:
    relative = path.relative_to(root)

    return any(
        part in IGNORED_PARTS
        for part in relative.parts
    )
