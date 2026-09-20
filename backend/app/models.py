"""
Pydantic data models for the Executive Productivity Agent.

Layer hierarchy:
  SourceDocument → Evidence → Commitment → DailyBrief / AnswerResponse
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ─── People ──────────────────────────────────────────────────────────────────

KNOWN_PERSONS = {
    "Arjun Malhotra": "arjun",
    "Neha Kapoor": "neha",
    "Raghav Sethi": "raghav",
    "Divya Rao": "divya",
    "Priya Nair": "priya",
    "Facilities": "facilities",
}

ARJUN = "Arjun Malhotra"


# ─── Source Layer ─────────────────────────────────────────────────────────────

class SourceType(str, Enum):
    meeting = "meeting"
    email = "email"
    voice_note = "voice_note"
    calendar = "calendar"


class SourceDocument(BaseModel):
    source_id: str                  # e.g. "meeting_21sep", "email_vl_2"
    source_type: SourceType
    date: str                       # ISO 8601 date "2026-09-21"
    time: str | None = None         # "09:50" if available
    participants: list[str] = Field(default_factory=list)
    raw_text: str
    label: str                      # Human-readable: "Leadership Sync — 21 Sep"


# ─── Evidence Layer ───────────────────────────────────────────────────────────

class Evidence(BaseModel):
    evidence_id: str
    date: str                       # ISO 8601 date
    time: str | None = None
    source: SourceDocument
    speaker: str | None = None      # Who said/wrote this (canonical name)
    excerpt: str                    # Exact quote from the source
    extracted_fact: str             # Human-readable extracted meaning
    updates_deadline: bool = False  # True if this evidence moves a prior deadline
    implies_completion: bool = False  # True if this suggests task is done


# ─── Commitment Layer ─────────────────────────────────────────────────────────

class OwnershipStatus(str, Enum):
    confirmed = "confirmed"   # All evidence definitively names one owner
    suggested = "suggested"   # At least one source suggests but does not confirm
    unknown = "unknown"       # Explicitly ambiguous or "flag it, don't assume"


class CommitmentStatus(str, Enum):
    outstanding = "outstanding"
    overdue = "overdue"
    due_today = "due_today"
    completed = "completed"
    unclear = "unclear"


class CommitmentCategory(str, Enum):
    my_action = "my_action"
    waiting_on_others = "waiting_on_others"
    ownership_unclear = "ownership_unclear"


class Commitment(BaseModel):
    commitment_id: str
    title: str
    description: str

    owner: str                          # Canonical name or "UNKNOWN"
    ownership_status: OwnershipStatus
    owner_display: str                  # "Arjun Malhotra" or "UNKNOWN — needs confirmation"

    recipient: str | None = None
    category: CommitmentCategory

    deadline_original: str | None = None     # ISO datetime string
    deadline_original_label: str | None = None
    deadline_latest: str | None = None       # ISO datetime string (most recent)
    deadline_latest_label: str | None = None

    status: CommitmentStatus

    evidence: list[Evidence] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)

    confidence: Literal["high", "medium", "low"] = "high"
    extraction_notes: str | None = None


# ─── API Response Layer ───────────────────────────────────────────────────────

class DailyBrief(BaseModel):
    as_of_date: str
    executive: str = ARJUN
    my_actions: list[Commitment] = Field(default_factory=list)
    waiting_on_others: list[Commitment] = Field(default_factory=list)
    ownership_unclear: list[Commitment] = Field(default_factory=list)


class QueryRequest(BaseModel):
    question: str
    as_of_date: str = "2026-09-23"


class ReasoningStep(BaseModel):
    step: int
    label: str
    detail: str
    status: Literal["success", "pending", "error"] = "success"


class AnswerResponse(BaseModel):
    answer: str
    commitments_cited: list[Commitment] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "high"
    reasoning_steps: list[ReasoningStep] = Field(default_factory=list)
