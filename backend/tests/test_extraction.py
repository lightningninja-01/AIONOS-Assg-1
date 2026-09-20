"""
Tests for the commitment extraction pipeline.
Compares LLM extraction output against the reference dataset.
Note: These tests call the real Groq API — set GROQ_API_KEY in .env.
"""
import json
import pytest
import asyncio
from pathlib import Path

pytestmark = pytest.mark.asyncio


@pytest.fixture
def reference():
    ref_path = Path(__file__).parent.parent / "data" / "reference" / "expected_commitments.json"
    return json.loads(ref_path.read_text())["commitments"]


@pytest.fixture
async def store(shared_store):
    return shared_store

async def test_expected_commitment_count(store, reference):
    """We expect 5 distinct commitments after deduplication."""
    commitments = store.all()
    assert len(commitments) == len(reference), (
        f"Expected {len(reference)} commitments, got {len(commitments)}: "
        f"{[c.commitment_id for c in commitments]}"
    )


async def test_commitment_ids_present(store, reference):
    """All expected IDs should be present."""
    extracted_ids = {c.commitment_id for c in store.all()}
    reference_ids = {r["id"] for r in reference}
    missing = reference_ids - extracted_ids
    assert not missing, f"Missing commitment IDs: {missing}"


async def test_vendor_list_evidence_count(store):
    """C1 (vendor list) should have evidence from at least 4 sources."""
    c1 = store.get("C1")
    assert c1 is not None, "C1 (vendor list) not found"
    ref_min = 4  # meeting + at least 3 emails (vl_2, vl_4, vl_5 minimally)
    assert len(c1.evidence) >= ref_min, (
        f"C1 should have at least {ref_min} evidence items, got {len(c1.evidence)}"
    )


async def test_arjun_is_owner_of_vendor_list(store):
    """Arjun must be the confirmed owner of C1."""
    c1 = store.get("C1")
    assert c1 is not None
    assert "Arjun" in c1.owner, f"C1 owner should be Arjun, got: {c1.owner}"
    from app.models import OwnershipStatus
    assert c1.ownership_status == OwnershipStatus.confirmed
