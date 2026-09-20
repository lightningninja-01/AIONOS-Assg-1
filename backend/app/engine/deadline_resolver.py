"""
Deadline resolver — deterministic.

Walks the evidence timeline (sorted by date) to determine:
  - deadline_original: first deadline mentioned
  - deadline_latest: most recent deadline (after any updates)

Evidence items that mention a different (later or earlier) deadline
compared to the previous one are flagged with updates_deadline=True.
"""
from __future__ import annotations

from app.ingestion.normalizer import normalize_deadline
from app.models import Evidence
from app.utils.logger import get_logger

log = get_logger(__name__)


def resolve_deadlines(
    evidence_list: list[Evidence],
    raw_deadline: str,
    source_date: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """
    Returns:
      (deadline_original_iso, deadline_original_label,
       deadline_latest_iso, deadline_latest_label)
    """
    # Start with the representative deadline from extraction
    orig_iso, orig_label = normalize_deadline(raw_deadline, source_date)

    # Walk all evidence sorted by date to find deadline updates
    sorted_evidence = sorted(evidence_list, key=lambda e: (e.date, e.time or "00:00"))

    prev_iso = orig_iso
    latest_iso = orig_iso
    latest_label = orig_label

    for ev in sorted_evidence:
        # Look for deadline-related language in the excerpt
        new_iso, new_label = _extract_deadline_from_excerpt(ev.excerpt, ev.date)
        if new_iso and new_iso != prev_iso:
            # This evidence updates the deadline
            ev.updates_deadline = True
            latest_iso = new_iso
            latest_label = new_label
            prev_iso = new_iso

    return orig_iso, orig_label, latest_iso, latest_label


def _extract_deadline_from_excerpt(excerpt: str, source_date: str) -> tuple[str | None, str]:
    """Try to find a deadline expression in an excerpt."""
    from app.ingestion.normalizer import normalize_deadline

    deadline_phrases = [
        "tomorrow morning",
        "by tomorrow",
        "wednesday morning",
        "thursday morning",
        "wednesday evening",
        "friday",
        "end of day",
        "eod",
        "this morning",
        "today",
        "by morning",
        "first thing",
    ]

    excerpt_lower = excerpt.lower()
    for phrase in deadline_phrases:
        if phrase in excerpt_lower:
            return normalize_deadline(phrase, source_date)

    return None, ""
