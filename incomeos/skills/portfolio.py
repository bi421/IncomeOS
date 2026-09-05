from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .profile_builder import ProfileReport, build_profile


@dataclass(frozen=True)
class PortfolioReport:
    repositories: tuple[ProfileReport, ...]

    @property
    def repository_count(self) -> int:
        return len(self.repositories)

    @property
    def total_skill_count(self) -> int:
        return sum(
            report.skill_count
            for report in self.repositories
        )


def build_portfolio(
    root: str | Path,
) -> PortfolioReport:
    root_path = Path(root)

    reports: list[ProfileReport] = []

    for repository in sorted(root_path.iterdir()):
        if not repository.is_dir():
            continue

        if not (repository / ".git").exists():
            continue

        reports.append(
            build_profile(str(repository))
        )

    return PortfolioReport(
        repositories=tuple(reports)
    )
