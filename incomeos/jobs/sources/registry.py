"""Job source registry."""

from incomeos.jobs.sources.remoteok import RemoteOKSource
from incomeos.jobs.sources.weworkremotely import WeWorkRemotelySource
from incomeos.jobs.sources.public_apis import HimalayasSource, RemotiveSource


REAL_JOB_SOURCES = (
    HimalayasSource,
    RemotiveSource,
    RemoteOKSource,
    WeWorkRemotelySource,
)


def build_sources():
    """Build all currently enabled real job source adapters."""
    return tuple(source() for source in REAL_JOB_SOURCES)
