"""Tests for cross-source deduplication — verifies vendor list is ONE commitment."""
import pytest
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def store():
    from app.engine.commitment_store import CommitmentStore
    s = CommitmentStore()
    await s.build()
    return s


async def test_vendor_list_is_single_commitment(store):
    """The vendor list must NOT appear as multiple commitments."""
    vendor_commitments = [
        c for c in store.all()
        if "vendor" in c.title.lower() or "vendor" in c.description.lower()
    ]
    assert len(vendor_commitments) == 1, (
        f"Expected exactly 1 vendor list commitment, got {len(vendor_commitments)}: "
        f"{[c.title for c in vendor_commitments]}"
    )


async def test_vendor_list_has_multi_source_evidence(store):
    """C1 must have evidence from at least 2 different source types."""
    c1 = store.get("C1")
    assert c1 is not None
    source_types = {ev.source.source_type for ev in c1.evidence}
    assert len(source_types) >= 2, f"C1 should span ≥2 source types, got: {source_types}"


async def test_total_commitment_count(store):
    """After dedup, we should have 5 unique commitments (not 20+ raw extractions)."""
    total = len(store.all())
    assert 3 <= total <= 7, f"Expected 5 (±2) commitments after dedup, got {total}"


async def test_meridian_call_is_single_commitment(store):
    """Meridian Logistics call confirmation must be a single commitment."""
    meridian_commitments = [
        c for c in store.all()
        if "meridian" in c.title.lower() or "meridian" in c.description.lower()
    ]
    assert len(meridian_commitments) == 1, (
        f"Meridian call should be 1 commitment, got {len(meridian_commitments)}"
    )
