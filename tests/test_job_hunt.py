from incomeos.job_hunt.hunter import JobHunter
from incomeos.jobs.models.job import Job


class FakeSource:
    def __init__(self, name, jobs=None, error=None):
        self.source_name = name
        self.jobs = jobs or []
        self.error = error

    def fetch(self):
        if self.error:
            raise RuntimeError(self.error)
        yield from self.jobs


def test_hunt_fetches_deduplicates_and_ranks(tmp_path):
    jobs = [
        Job("fake", "Python Automation Engineer", "https://EXAMPLE.com/a", "A", "Python Docker"),
        Job("fake", "Python Developer", "https://example.com/a", "A", "Python"),
        Job("other", "Python Automation Engineer", "https://example.com/a", "A", "Python Docker"),
        Job("fake", "C++ Engineer", "https://example.com/b", "B", "C++ Python"),
    ]
    report = JobHunter(tmp_path).hunt(
        ["Python", "Docker"],
        sources=[FakeSource("fake", jobs[:2]), FakeSource("other", jobs[2:])],
        limit=10,
    )

    assert len(report.items) == 2
    assert report.items[0].url == "https://example.com/a"
    assert report.items[0].fit_score == 1.0
    assert report.items[0].matched_skills == ("Python", "Docker")
    assert report.sources[0].fetched == 2
    assert report.sources[0].accepted == 1
    assert not report.sources[0].failed


def test_hunt_keeps_source_failure_visible(tmp_path):
    report = JobHunter(tmp_path).hunt(["Python"], sources=[FakeSource("broken", error="timeout")])

    assert report.items == ()
    assert report.failed_sources == ("broken",)
    assert report.sources[0].error == "timeout"


def test_hunt_rejects_invalid_bounds(tmp_path):
    hunter = JobHunter(tmp_path)
    try:
        hunter.hunt(["Python"], limit=0)
        assert False
    except ValueError:
        pass

    try:
        hunter.hunt(["Python"], minimum_fit=1.1)
        assert False
    except ValueError:
        pass



def test_hunt_reports_source_provenance_and_acceptance_rate(tmp_path):
    job = Job("fake", "Python Developer", "https://example.com/a", "A", "Python")
    report = JobHunter(tmp_path).hunt(
        ["Python"],
        sources=[FakeSource("fake", [job])],
        limit=1,
    )
    health = report.sources[0]
    assert health.protocol == "unknown"
    assert health.provider_type == "unclassified"
    assert health.endpoint == ""
    assert health.observed_at
    assert health.acceptance_rate == 1.0


def test_known_source_descriptor_is_explicit():
    from incomeos.job_hunt.source_evidence import descriptor_for

    descriptor = descriptor_for("himalayas")
    assert descriptor.endpoint == "https://himalayas.app/jobs/api"
    assert descriptor.protocol == "HTTPS JSON API"
