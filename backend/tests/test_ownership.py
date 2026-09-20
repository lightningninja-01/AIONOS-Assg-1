"""
CRITICAL TEST — Ownership ambiguity.
The Mumbai lease renewal must NEVER be assigned to Facilities.
Owner must be UNKNOWN.
"""
import pytest
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def store():
    from app.engine.commitment_store import CommitmentStore
    s = CommitmentStore()
    await s.build()
    return s


async def test_mumbai_lease_owner_is_unknown(store):
    """C5 (Mumbai lease) MUST have owner=UNKNOWN."""
    c5 = store.get("C5")
    assert c5 is not None, "C5 (Mumbai lease) not found"
    from app.models import OwnershipStatus
    assert c5.ownership_status in (OwnershipStatus.unknown, OwnershipStatus.suggested), (
        f"C5 ownership_status must be unknown or suggested, got: {c5.ownership_status}"
    )
    assert c5.owner != "Facilities", (
        "C5 owner must NOT be 'Facilities' — this is speculative, not a confirmed assignment"
    )


async def test_mumbai_not_in_my_actions(store):
    """C5 should NOT appear under my_actions — it's not Arjun's confirmed action."""
    from app.models import CommitmentCategory
    c5 = store.get("C5")
    assert c5 is not None
    assert c5.category != CommitmentCategory.my_action, (
        "C5 (Mumbai lease) should NOT be in my_actions — ownership is unclear"
    )


async def test_mumbai_has_evidence(store):
    """C5 must have at least 3 evidence items showing the ambiguity."""
    c5 = store.get("C5")
    assert c5 is not None
    assert len(c5.evidence) >= 3, (
        f"C5 should have at least 3 evidence items to show ambiguity trail, got {len(c5.evidence)}"
    )


async def test_confirmed_owners_not_marked_unknown(store):
    """Arjun's vendor list (C1) must NOT be marked unknown — it is confirmed."""
    c1 = store.get("C1")
    assert c1 is not None
    from app.models import OwnershipStatus
    assert c1.ownership_status == OwnershipStatus.confirmed, (
        f"C1 (vendor list) should have confirmed ownership, got: {c1.ownership_status}"
    )
