"""
LLM service for the Q&A agent.

Uses Groq (openai/gpt-oss-20b) with tool-calling to ensure
structured, grounded answers. The LLM must cite commitment IDs
and cannot fabricate information.

Adapted from the Omni-Channel LLMService pattern.
"""
from __future__ import annotations

import json

from groq import AsyncGroq

from app.config.settings import get_settings
from app.models import Commitment
from app.utils.logger import get_logger

log = get_logger(__name__)

ANSWER_TOOL = {
    "type": "function",
    "function": {
        "name": "answer_query",
        "description": "Provide a grounded answer to the executive's question, citing the relevant commitment IDs.",
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": (
                        "A clear, concise answer for Arjun Malhotra. "
                        "If ownership is unclear, explicitly state it is unclear. "
                        "Never invent or speculate beyond what the data shows."
                    )
                },
                "commitment_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of commitment IDs (e.g. ['C1', 'C5']) that this answer draws from."
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "How confident you are in this answer based on the available evidence."
                }
            },
            "required": ["answer", "commitment_ids", "confidence"]
        }
    }
}

SYSTEM_PROMPT = """You are Arjun Malhotra's AI Executive Assistant at Veridian Corp.

Your job is to answer questions about Arjun's commitments, promises, and action items for the week of 21–25 September 2026.

STRICT RULES:
1. Answer ONLY using the commitment data provided in the context block below. Do NOT invent or infer beyond what is stated.
2. If ownership of a task is marked as UNKNOWN or "needs confirmation", you MUST state that ownership is unclear. Never assign an owner based on speculation.
3. If a commitment is COMPLETED, say so clearly.
4. If a commitment is OVERDUE, say so clearly.
5. Always cite which commitment IDs your answer draws from — you MUST call the answer_query tool.
6. Keep answers concise and actionable. Arjun is busy.

People context:
- Arjun Malhotra: VP Sales (the user — "you")
- Neha Kapoor: Marketing Lead
- Raghav Sethi: Ops Manager
- Divya Rao: Finance
- Priya Nair: Client at Meridian Logistics
- Facilities: Internal distribution list

When you refer to "you" or "your", you mean Arjun Malhotra.
"""


class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncGroq(api_key=settings.groq_api_key, timeout=settings.groq_timeout)
        self._model = settings.groq_model

    async def answer(
        self,
        question: str,
        context_block: str,
        as_of_date: str,
    ) -> tuple[str, list[str], str]:
        """
        Returns (answer_text, commitment_ids_cited, confidence).
        """
        user_message = f"""Simulated current date: {as_of_date}

--- COMMITMENT DATA ---
{context_block}
--- END COMMITMENT DATA ---

Question: {question}"""

        max_retries = 3
        backoff = 0.5
        import asyncio

        for attempt in range(max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    tools=[ANSWER_TOOL],
                    tool_choice={"type": "function", "function": {"name": "answer_query"}},
                    temperature=0.2,
                )

                msg = response.choices[0].message
                if msg.tool_calls:
                    args = json.loads(msg.tool_calls[0].function.arguments)
                    return (
                        args.get("answer", "I could not find a relevant answer."),
                        args.get("commitment_ids", []),
                        args.get("confidence", "medium"),
                    )

                # Fallback if tool not called
                return (msg.content or "I could not find a relevant answer.", [], "low")

            except Exception as exc:
                exc_str = str(exc)
                is_transient = any(
                    s in exc_str for s in ["503", "429", "rate_limit", "overloaded", "UNAVAILABLE"]
                )
                if is_transient and attempt < max_retries - 1:
                    log.warning(f"Groq transient error (attempt {attempt + 1}): {exc!r}. Retrying in {backoff}s")
                    await asyncio.sleep(backoff)
                    backoff *= 2
                else:
                    log.error(f"Groq failed after {attempt + 1} attempts: {exc!r}")
                    raise

        return ("An error occurred while processing your question.", [], "low")
