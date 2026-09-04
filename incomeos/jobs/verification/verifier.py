"""Job truth and freshness verification.

Real implementation. Does NOT claim to verify that a job is still
accepting applications (that requires a live network check the caller
can opt into separately - see verify_job_live). This function verifies
what can be checked for free, deterministically, from the record itself:

  - required fields are present and non-placeholder
  - the URL is a well-formed http(s) link
  - the source is one of the registered adapters

A job that fails this is not necessarily fake - it may just be
incomplete - but it should not be presented to the user as
application-ready without a human glancing at it first.
"""

from __future__ import annotations

from urllib.parse import urlparse

from incomeos.jobs.models.job import Job

_KNOWN_SOURCES = {"arbeitnow", "remoteok", "weworkremotely"}
_PLACEHOLDER_TITLES = {"", "untitled", "unknown"}
_PLACEHOLDER_COMPANIES = {"", "unknown"}


def verify_job(job: Job) -> bool:
    """Verify job evidence/status using only the record we already have."""
    if (job.title or "").strip().lower() in _PLACEHOLDER_TITLES:
        return False
    if (job.company or "").strip().lower() in _PLACEHOLDER_COMPANIES:
        return False

    url = job.url or job.source_url
    if not url:
        return False
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False

    if (job.source or "").strip().lower() not in _KNOWN_SOURCES:
        return False

    return True


def verify_job_live(job: Job, timeout: float = 8.0) -> bool:
    """Optional network check: does the job URL still respond?

    Separate from verify_job() on purpose - callers that are verifying
    hundreds of jobs at once should not be forced to make hundreds of
    HTTP requests just to rank them. Call this only for the handful of
    jobs a user is about to actually apply to.
    """
    import urllib.request

    if not verify_job(job):
        return False

    req = urllib.request.Request(job.url or job.source_url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False