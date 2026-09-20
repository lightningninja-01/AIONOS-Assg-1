"""
Status resolver — fully deterministic.

Given a commitment and the simulated current date,
calculates the appropriate CommitmentStatus.

No LLM involved here.
"""
from __future__ import annotations

from app.models import CommitmentStatus, Evidence
from app.utils.logger import get_logger

log = get_logger(__name__)


def resolve_status(
    deadline_latest_iso: str | None,
    evidence_list: list[Evidence],
    as_of_date: str,
) -> CommitmentStatus:
    """
    as_of_date: "YYYY-MM-DD"
    deadline_latest_iso: "YYYY-MM-DDTHH:MM:SS" or None
    """
    # Check for completion evidence first (date-gated)
    if _is_completed(evidence_list, as_of_date):
        return CommitmentStatus.completed

    if deadline_latest_iso is None:
        return CommitmentStatus.unclear

    deadline_date = deadline_latest_iso[:10]  # "YYYY-MM-DD"

    if deadline_date < as_of_date:
        return CommitmentStatus.overdue
    elif deadline_date == as_of_date:
        return CommitmentStatus.due_today
    else:
        return CommitmentStatus.outstanding


def _is_completed(evidence_list: list[Evidence], as_of_date: str) -> bool:
    """Return True if any evidence on or before as_of_date implies completion."""
    for ev in evidence_list:
        if ev.implies_completion and ev.date <= as_of_date:
            return True
    return False


def resolve_category(
    owner: str,
    ownership_status: str,
    as_of_date: str,
    status: CommitmentStatus,
    title: str = "",
) -> str:
    from app.models import CommitmentCategory, OwnershipStatus

    if ownership_status in (OwnershipStatus.unknown.value, OwnershipStatus.suggested.value, "unknown", "suggested"):
        return CommitmentCategory.ownership_unclear.value

    # Deterministic check for blocked/waiting actions
    title_lower = title.lower()
    if "from " in title_lower or "waiting" in title_lower:
        return CommitmentCategory.waiting_on_others.value

    if owner == "Arjun Malhotra":
        return CommitmentCategory.my_action.value

    return CommitmentCategory.waiting_on_others.value
