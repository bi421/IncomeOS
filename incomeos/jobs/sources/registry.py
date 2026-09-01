"""Job source registry."""

from incomeos.jobs.sources.arbeitnow import ArbeitnowSource
from incomeos.jobs.sources.remoteok import RemoteOKSource
from incomeos.jobs.sources.weworkremotely import WeWorkRemotelySource


REAL_JOB_SOURCES = (
    RemoteOKSource,
    ArbeitnowSource,
    WeWorkRemotelySource,
)


def build_sources():
    """Build all currently enabled real job source adapters."""
    return tuple(source() for source in REAL_JOB_SOURCES)
