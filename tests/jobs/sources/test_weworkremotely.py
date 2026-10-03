from incomeos.jobs.sources.weworkremotely import WeWorkRemotelySource


def test_wwr_source_does_not_use_fetch_time_when_pubdate_missing(monkeypatch):
    rss = """<?xml version="1.0"?>
    <rss><channel>
      <item>
        <title>Acme: Python Engineer</title>
        <link>https://example.com/undated</link>
        <description>Python backend engineering.</description>
      </item>
    </channel></rss>"""

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None
        def read(self):
            return rss.encode("utf-8")

    monkeypatch.setattr(
        "incomeos.jobs.sources.weworkremotely.urllib.request.urlopen",
        lambda request, timeout: Response(),
    )

    jobs = list(WeWorkRemotelySource().fetch())
    assert len(jobs) == 1
    assert jobs[0].created_at == ""
