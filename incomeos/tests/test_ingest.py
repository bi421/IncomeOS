import pytest
import asyncio
from incomeos.ingest import IngestPipeline
from incomeos.storage.models import JobOffer

@pytest.mark.asyncio
async def test_ingest_pipeline():
    pipeline = IngestPipeline()
    results = await pipeline.run(limit=5)
    assert len(results) == 5
    for item in results:
        offer = JobOffer(**item)
        assert offer.title
        assert offer.url
