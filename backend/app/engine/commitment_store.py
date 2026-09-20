"""
Commitment store — orchestrates the full pipeline at startup.

Pipeline:
  load_all_sources()
    → extract_all() [LLM]
      → deduplicate() [deterministic + LLM pair scoring]
        → deadline_resolver [deterministic]
          → ownership_classifier [rule-based]
            → status_resolver [deterministic]
              → CommitmentStore (in-memory)

The store is populated once and serves all API requests.
"""
from __future__ import annotations

import uuid
from typing import Any

from app.config.settings import get_settings
from app.engine.deadline_resolver import resolve_deadlines
from app.engine.deduplicator import Deduplicator
from app.engine.extractor import CommitmentExtractor
from app.engine.ownership_classifier import classify_ownership
from app.engine.status_resolver import resolve_category, resolve_status
from app.ingestion.loader import load_all_sources
from app.models import (
    ARJUN,
    Commitment,
    CommitmentCategory,
    CommitmentStatus,
    Evidence,
    OwnershipStatus,
)
from app.utils.logger import get_logger

log = get_logger(__name__)

_COMMITMENT_ID_MAP = {
    "vendor_list__raghav_sethi": "C1",
    "q3_campaign_deck__arjun_malhotra": "C2",
    "q3_campaign_deck__none": "C2",
    "meridian_call__priya_nair": "C3",
    "meridian_call__none": "C3",
    "expense_report__arjun_malhotra": "C4",
    "expense_report__none": "C4",
    "mumbai_lease__none": "C5",
}


class CommitmentStore:
    def __init__(self) -> None:
        self._commitments: list[Commitment] = []
        self._ready = False

    async def build(self) -> None:
        """Run the full pipeline and populate the store."""
        settings = get_settings()
        log.info("CommitmentStore: starting pipeline build...")

        # Step 1: Load sources
        sources = load_all_sources()

        # Step 2: LLM extraction
        extractor = CommitmentExtractor()
        candidates = await extractor.extract_all(sources)

        # Step 3: Deduplication
        deduplicator = Deduplicator()
        merged = await deduplicator.deduplicate(candidates)

        # Step 4–7: Build final Commitment objects
        commitments = []
        counter = 1
        for semantic_key, (rep_raw, evidence_list) in merged.items():
            commitment = self._build_commitment(
                semantic_key=semantic_key,
                rep_raw=rep_raw,
                evidence_list=evidence_list,
                counter=counter,
                as_of_date=settings.simulated_today,
            )
            commitments.append(commitment)
            counter += 1

        self._commitments = sorted(commitments, key=lambda c: c.commitment_id)
        self._ready = True
        log.info(f"CommitmentStore ready: {len(self._commitments)} commitments")

    def _build_commitment(
        self,
        semantic_key: str,
        rep_raw: dict[str, Any],
        evidence_list: list[Evidence],
        counter: int,
        as_of_date: str,
    ) -> Commitment:
        # Assign friendly ID
        cid = _COMMITMENT_ID_MAP.get(semantic_key, f"C{counter}")

        # Resolve deadlines
        raw_deadline = rep_raw.get("deadline", "UNKNOWN")
        source_date = evidence_list[0].date if evidence_list else as_of_date

        orig_iso, orig_label, latest_iso, latest_label = resolve_deadlines(
            evidence_list, raw_deadline, source_date
        )

        # Classify ownership
        raw_owner = rep_raw.get("owner", "UNKNOWN")
        raw_confidence = rep_raw.get("ownership_confidence", "unknown")
        owner, ownership_status, owner_display = classify_ownership(
            raw_owner, raw_confidence, evidence_list
        )

        # Resolve status
        status = resolve_status(latest_iso, evidence_list, as_of_date)

        # Resolve category
        category_str = resolve_category(owner, ownership_status.value, as_of_date, status, title=rep_raw.get("description", ""))
        category = CommitmentCategory(category_str)

        # Determine recipient
        recipient = rep_raw.get("recipient") or None
        if recipient and recipient.strip().lower() in ("none", "null", "n/a", ""):
            recipient = None

        # Collect unique source_ids
        source_ids = list({ev.source.source_id for ev in evidence_list})

        # Sort evidence by date
        sorted_evidence = sorted(evidence_list, key=lambda e: (e.date, e.time or "00:00"))

        return Commitment(
            commitment_id=cid,
            title=_make_title(rep_raw.get("description", ""), owner, recipient),
            description=rep_raw.get("description", ""),
            owner=owner,
            ownership_status=ownership_status,
            owner_display=owner_display,
            recipient=recipient,
            category=category,
            deadline_original=orig_iso,
            deadline_original_label=orig_label,
            deadline_latest=latest_iso,
            deadline_latest_label=latest_label,
            status=status,
            evidence=sorted_evidence,
            source_ids=source_ids,
            confidence="high" if raw_confidence == "confirmed" else "medium",
            extraction_notes=None,
        )

    def all(self) -> list[Commitment]:
        return list(self._commitments)

    def get(self, commitment_id: str) -> Commitment | None:
        for c in self._commitments:
            if c.commitment_id == commitment_id:
                return c
        return None

    def get_many(self, ids: list[str]) -> list[Commitment]:
        return [c for c in self._commitments if c.commitment_id in ids]

    @property
    def is_ready(self) -> bool:
        return self._ready


def _make_title(description: str, owner: str, recipient: str | None) -> str:
    """Create a concise title from description."""
    # Truncate to ~60 chars
    desc = description.strip()
    if len(desc) > 60:
        desc = desc[:57] + "..."
    return desc
