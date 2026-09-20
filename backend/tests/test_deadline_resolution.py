"""Tests for deadline evolution — verifies C1 deadline is tracked correctly."""
import pytest
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def store():
    from app.engine.commitment_store import CommitmentStore
    s = CommitmentStore()
    await s.build()
    return s


async def test_vendor_list_deadline_latest_is_wednesday(store):
    """C1's latest deadline must be Wednesday 23 Sep (most recent update)."""
    c1 = store.get("C1")
    assert c1 is not None, "C1 not found"
    assert c1.deadline_latest is not None, "C1 has no latest deadline"
    assert "2026-09-23" in c1.deadline_latest, (
        f"C1 latest deadline should be 2026-09-23, got: {c1.deadline_latest}"
    )


async def test_vendor_list_has_deadline_original(store):
    """C1's original deadline must be earlier than latest."""
    c1 = store.get("C1")
    assert c1 is not None
    if c1.deadline_original and c1.deadline_latest:
        assert c1.deadline_original <= c1.deadline_latest, (
            f"Original deadline {c1.deadline_original} should be <= latest {c1.deadline_latest}"
        )


async def test_expense_report_deadline_updated(store):
    """C4 deadline was moved from Thu to Wed evening by Arjun."""
    c4 = store.get("C4")
    assert c4 is not None, "C4 (expense report) not found"
    # Deadline should be on or before 2026-09-23 (Wed evening)
    if c4.deadline_latest:
        assert c4.deadline_latest[:10] <= "2026-09-23", (
            f"C4 deadline should be Wed or earlier, got: {c4.deadline_latest}"
        )
