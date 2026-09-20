"""
LangGraph 3-node Q&A graph.

Nodes:
  1. context_loader  — loads commitments and formats context block
  2. llm_reasoning   — calls Groq to answer with cited commitment IDs
  3. response_builder — attaches full Evidence to cited commitments

Adapted from the Omni-Channel project's graph/builder.py pattern.
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agent.llm_service import LLMService
from app.agent.state import AgentState
from app.engine.commitment_store import CommitmentStore
from app.models import AnswerResponse, ReasoningStep
from app.utils.logger import get_logger

log = get_logger(__name__)


def _format_context_block(commitments, as_of_date: str) -> str:
    """Format all commitments into a structured text block for the LLM."""
    lines = []
    for c in commitments:
        lines.append(f"\n=== COMMITMENT {c.commitment_id}: {c.title} ===")
        lines.append(f"Owner: {c.owner_display}")
        lines.append(f"Ownership status: {c.ownership_status.value}")
        lines.append(f"Recipient: {c.recipient or 'N/A'}")
        lines.append(f"Category: {c.category.value}")
        lines.append(f"Original deadline: {c.deadline_original_label or 'UNKNOWN'}")
        lines.append(f"Latest deadline: {c.deadline_latest_label or 'UNKNOWN'}")
        lines.append(f"Status (as of {as_of_date}): {c.status.value.upper()}")
        lines.append("Evidence timeline:")
        for ev in c.evidence:
            completion_flag = " [COMPLETION]" if ev.implies_completion else ""
            deadline_flag = " [DEADLINE UPDATED]" if ev.updates_deadline else ""
            lines.append(
                f"  [{ev.date} {ev.time or ''}] {ev.source.source_type.value} — "
                f"{ev.source.label}{completion_flag}{deadline_flag}"
            )
            lines.append(f"    Excerpt: \"{ev.excerpt}\"")
            lines.append(f"    Fact: {ev.extracted_fact}")
    return "\n".join(lines)


def build_qa_graph(store: CommitmentStore, llm: LLMService):
    """Build and compile the LangGraph Q&A state machine."""

    # ─── Node 1: Context Loader ────────────────────────────────────────────────
    async def context_loader(state: AgentState) -> AgentState:
        log.info(f"[context_loader] Loading context for question: {state['question'][:60]}...")
        all_commitments = store.all()
        context = _format_context_block(all_commitments, state["as_of_date"])
        return {
            **state,
            "all_commitments": all_commitments,
            "context_block": context,
        }

    # ─── Node 2: LLM Reasoning ────────────────────────────────────────────────
    async def llm_reasoning(state: AgentState) -> AgentState:
        log.info("[llm_reasoning] Calling Groq for answer...")
        try:
            answer, cited_ids, confidence = await llm.answer(
                question=state["question"],
                context_block=state["context_block"],
                as_of_date=state["as_of_date"],
            )
            log.info(f"[llm_reasoning] Answer generated. Cited: {cited_ids}")
            return {
                **state,
                "raw_answer": answer,
                "cited_ids": cited_ids,
                "confidence": confidence,
                "error": None,
            }
        except Exception as exc:
            log.error(f"[llm_reasoning] Failed: {exc!r}")
            return {
                **state,
                "raw_answer": "I encountered an error while processing your question. Please try again.",
                "cited_ids": [],
                "confidence": "low",
                "error": str(exc),
            }

    # ─── Node 3: Response Builder ─────────────────────────────────────────────
    async def response_builder(state: AgentState) -> AgentState:
        log.info("[response_builder] Attaching evidence to cited commitments...")
        cited_commitments = store.get_many(state.get("cited_ids", []))

        reasoning_steps = [
            ReasoningStep(
                step=1,
                label="Context loaded",
                detail=f"{len(state.get('all_commitments', []))} commitments loaded for {state['as_of_date']}",
                status="success",
            ),
            ReasoningStep(
                step=2,
                label="LLM reasoning",
                detail=(
                    f"Groq identified {', '.join(state.get('cited_ids', [])) or 'no specific commitments'} as relevant"
                    if not state.get("error") else f"Error: {state.get('error')}"
                ),
                status="error" if state.get("error") else "success",
            ),
            ReasoningStep(
                step=3,
                label="Evidence attached",
                detail=f"{sum(len(c.evidence) for c in cited_commitments)} evidence items from {len(cited_commitments)} commitment(s)",
                status="success",
            ),
        ]

        response = AnswerResponse(
            answer=state.get("raw_answer", ""),
            commitments_cited=cited_commitments,
            confidence=state.get("confidence", "medium"),
            reasoning_steps=reasoning_steps,
        )
        return {**state, "response": response}

    # ─── Assemble Graph ───────────────────────────────────────────────────────
    graph = StateGraph(AgentState)
    graph.add_node("context_loader", context_loader)
    graph.add_node("llm_reasoning", llm_reasoning)
    graph.add_node("response_builder", response_builder)

    graph.set_entry_point("context_loader")
    graph.add_edge("context_loader", "llm_reasoning")
    graph.add_edge("llm_reasoning", "response_builder")
    graph.add_edge("response_builder", END)

    return graph.compile()
