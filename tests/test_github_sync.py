from incomeos.core.github import GitHubRepository


def test_repository_model():
    repo = GitHubRepository(
        name="ResearchOS",
        url="https://github.com/bi421/ResearchOS",
        is_private=False,
        is_fork=False,
        is_archived=False,
    )

    assert repo.name == "ResearchOS"
    assert repo.is_private is False
    assert repo.is_fork is False
    assert repo.is_archived is False