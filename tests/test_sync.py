from incomeos.core.github import GitHubRepository
from incomeos.core.sync import SyncResult


def test_sync_result():
    repository = GitHubRepository(
        name="ResearchOS",
        url="https://github.com/bi421/ResearchOS",
        is_private=False,
        is_fork=False,
        is_archived=False,
    )

    result = SyncResult(
        repository=repository,
        local_path="data/github_repos/ResearchOS",
    )

    assert result.repository.name == "ResearchOS"
    assert "ResearchOS" in str(result.local_path)