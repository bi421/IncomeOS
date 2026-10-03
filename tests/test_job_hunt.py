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


def _job(title, url, company, description, **raw):
    return Job("fake", title, url, company, description, raw_data=raw)


def test_hunt_fetches_deduplicates_ranks_and_requires_eligibility(tmp_path):
    jobs = [
        _job("Python Automation Engineer", "https://EXAMPLE.com/a", "A", "Python Docker",
             candidate_required_location=["Mongolia"]),
        _job("Python Developer", "https://example.com/a", "A", "Python",
             candidate_required_location=["Mongolia"]),
        _job("Python Automation Engineer", "https://example.com/a", "A", "Python Docker",
             candidate_required_location=["Mongolia"]),
        _job("C++ Engineer", "https://example.com/b", "B", "C++ Python",
             candidate_required_location=["Mongolia"]),
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


def test_hunt_rejects_unrelated_jobs_even_when_minimum_fit_is_zero(tmp_path):
    unrelated = _job(
        "Marketing Manager", "https://example.com/m", "A",
        "Excel and marketing", candidate_required_location=["Mongolia"]
    )
    report = JobHunter(tmp_path).hunt(
        ["Python"], sources=[FakeSource("fake", [unrelated])], limit=10
    )
    assert report.items == ()
    assert report.sources[0].accepted == 0


def test_hunt_rejects_unknown_location_and_accepts_explicit_target(tmp_path):
    generic_remote = _job(
        "Python Developer", "https://example.com/r", "A",
        "Remote Python developer"
    )
    mongolia = _job(
        "Python Developer", "https://example.com/m", "A", "Remote Python developer",
        candidate_required_location=["Mongolia"]
    )
    report = JobHunter(tmp_path).hunt(
        ["Python"], sources=[FakeSource("fake", [generic_remote, mongolia])], limit=10
    )
    assert len(report.items) == 1
    assert report.items[0].url == "https://example.com/m"


def test_hunt_keeps_source_failure_visible(tmp_path):
    report = JobHunter(tmp_path).hunt(["Python"], sources=[FakeSource("broken", error="timeout")])
    assert report.items == ()
    assert report.failed_sources == ("broken",)
    assert report.sources[0].error == "timeout"


def test_hunt_rejects_invalid_bounds(tmp_path):
    hunter = JobHunter(tmp_path)
    for kwargs in ({"limit": 0}, {"minimum_fit": 1.1}):
        try:
            hunter.hunt(["Python"], **kwargs)
            assert False
        except ValueError:
            pass


def test_hunt_reports_source_provenance_and_acceptance_rate(tmp_path):
    job = _job(
        "Python Developer", "https://example.com/a", "A", "Python",
        candidate_required_location=["Mongolia"]
    )
    report = JobHunter(tmp_path).hunt(
        ["Python"], sources=[FakeSource("fake", [job])], limit=1
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
