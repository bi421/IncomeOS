from incomeos.job_hunt.hunter import JobHunter
from incomeos.jobs.models.job import Job


class RotatingSource:
    source_name = "rotating"

    def __init__(self):
        self.calls = 0

    def fetch(self):
        self.calls += 1
        yield Job(
            "rotating",
            f"Python Job {self.calls}",
            f"https://example.com/jobs/{self.calls}",
            "Example",
            "Python",
        )


def test_repeated_hunt_performs_a_fresh_fetch(tmp_path):
    source = RotatingSource()
    hunter = JobHunter(tmp_path)

    first = hunter.hunt(["Python"], sources=[source], limit=2)
    second = hunter.hunt(["Python"], sources=[source], limit=2)

    assert source.calls == 2
    assert first.items[0].url == "https://example.com/jobs/1"
    assert second.items[0].url == "https://example.com/jobs/2"
