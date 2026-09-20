"""
Ownership classifier — rule-based + deterministic.

Determines the final OwnershipStatus for a commitment.

Priority rules:
  1. If ANY evidence contains "flag it" or "don't assume" → UNKNOWN (hard override)
  2. If all evidence agrees on one owner with confirmed confidence → confirmed
  3. If any evidence merely suggests an owner → suggested (surfaced as unclear in brief)
  4. Otherwise → unknown
"""
from __future__ import annotations

from app.models import Evidence, OwnershipStatus
from app.utils.logger import get_logger

log = get_logger(__name__)

# Phrases that force UNKNOWN regardless of other evidence
FORCE_UNKNOWN_PHRASES = [
    "flag it",
    "don't assume",
    "do not assume",
    "not sure whose",
    "don't think it's been assigned",
    "still unowned",
    "hasn't been assigned",
    "no one has",
    "unowned",
]


def classify_ownership(
    owner: str,
    ownership_confidence: str,
    evidence_list: list[Evidence],
) -> tuple[str, OwnershipStatus, str]:
    """
    Returns (owner, ownership_status, owner_display).
    """
    # Rule 1 — Hard override: explicit "flag it, don't assume" language in any evidence
    all_text = " ".join((ev.excerpt or "").lower() for ev in evidence_list)
    for phrase in FORCE_UNKNOWN_PHRASES:
        if phrase in all_text:
            log.info(f"Ownership forced UNKNOWN due to phrase: '{phrase}'")
            return "UNKNOWN", OwnershipStatus.unknown, "UNKNOWN — needs confirmation"

    # Rule 2 — All evidence confirms a single owner
    if ownership_confidence == "confirmed" and owner and owner != "UNKNOWN":
        return owner, OwnershipStatus.confirmed, owner

    # Rule 3 — Owner is only suggested/speculative
    if ownership_confidence == "suggested" and owner and owner != "UNKNOWN":
        log.info(f"Ownership for '{owner}' is only suggested — surfacing as unclear")
        return owner, OwnershipStatus.suggested, f"{owner} (unconfirmed)"

    # Default: unknown
    return "UNKNOWN", OwnershipStatus.unknown, "UNKNOWN — needs confirmation"
