import pytest

from incomeos.core.github import list_repositories


@pytest.mark.integration
def test_github_inventory():
    repositories = list_repositories("bi421")

    assert len(repositories) >= 1
    assert any(
        repository.name == "ResearchOS"
        for repository in repositories
    )