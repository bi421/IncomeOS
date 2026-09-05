from incomeos.jobs.sources.public_apis import HimalayasSource, RemotiveSource


def test_himalayas_source_normalizes_and_filters(monkeypatch):
    payloads = iter(
        [
            {
                "jobs": [
                    {
                        "title": "Python Backend Engineer",
                        "applicationLink": "https://example.com/1",
                        "companyName": "Acme",
                        "description": "Build Python backend services.",
                        "categories": ["Engineering"],
                    }
                ]
            }
        ]
    )
    monkeypatch.setattr(HimalayasSource, "_get_json", lambda self, url: next(payloads))
    jobs = list(HimalayasSource().fetch())
    assert len(jobs) == 1
    assert jobs[0].source == "himalayas"
    assert jobs[0].company == "Acme"
    assert jobs[0].url == "https://example.com/1"


def test_remotive_source_normalizes_real_shape(monkeypatch):
    monkeypatch.setattr(
        RemotiveSource,
        "_get_json",
        lambda self, url: {
            "jobs": [
                {
                    "title": "Data Engineer",
                    "url": "https://example.com/2",
                    "company_name": "Acme Data",
                    "description": "Work on ETL and data pipelines.",
                    "category": "software development",
                    "publication_date": "2026-09-05T00:00:00Z",
                }
            ]
        },
    )
    jobs = list(RemotiveSource().fetch())
    assert len(jobs) == 1
    assert jobs[0].source == "remotive"
    assert jobs[0].company == "Acme Data"
    assert jobs[0].created_at.startswith("2026-09-05")
