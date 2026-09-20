"""
LangGraph agent state for the Q&A pipeline.
Adapted from the Omni-Channel project's ConversationState pattern.
"""
from __future__ import annotations

from typing import Any, TypedDict

from app.models import AnswerResponse, Commitment, ReasoningStep


class AgentState(TypedDict, total=False):
    # Input
    question: str
    as_of_date: str

    # Context loaded by context_loader node
    all_commitments: list[Commitment]
    context_block: str              # Formatted string injected into LLM prompt

    # LLM output
    raw_answer: str
    cited_ids: list[str]
    confidence: str

    # Final output
    response: AnswerResponse

    # Error handling
    error: str | None
