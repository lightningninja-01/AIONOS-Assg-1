"""
LLM Commitment Extractor.

For each SourceDocument, asks Groq to identify commitments using
structured tool-calling. Returns a list of candidate Commitment
objects with Evidence attached.

The LLM is constrained to:
  - Only report what the source explicitly states
  - Use known person names only
  - Mark ownership as UNKNOWN if not definitively established
  - Mark deadlines as UNKNOWN if not mentioned
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from groq import AsyncGroq

from app.config.settings import get_settings
from app.ingestion.normalizer import normalize_deadline
from app.models import (
    KNOWN_PERSONS,
    Commitment,
    CommitmentCategory,
    Evidence,
    OwnershipStatus,
    SourceDocument,
)
from app.utils.logger import get_logger

log = get_logger(__name__)

ARJUN = "Arjun Malhotra"

EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_commitments",
        "description": "Extract all commitments, promises, or action items from the provided source text.",
        "parameters": {
            "type": "object",
            "properties": {
                "commitments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "What was committed or promised, in plain English."
                            },
                            "owner": {
                                "type": "string",
                                "description": (
                                    "The person responsible for completing this action. "
                                    "Must be one of: 'Arjun Malhotra', 'Neha Kapoor', 'Raghav Sethi', "
                                    "'Divya Rao', 'Priya Nair', 'Facilities', or 'UNKNOWN'. "
                                    "Use UNKNOWN if there is any doubt or if ownership is only speculated."
                                )
                            },
                            "ownership_confidence": {
                                "type": "string",
                                "enum": ["confirmed", "suggested", "unknown"],
                                "description": (
                                    "confirmed = text definitively assigns this person. "
                                    "suggested = text implies or speculates. "
                                    "unknown = unclear or explicitly flagged as unresolved."
                                )
                            },
                            "recipient": {
                                "type": ["string", "null"],
                                "description": "Who receives or benefits from this action. Null if not mentioned."
                            },
                            "deadline": {
                                "type": "string",
                                "description": (
                                    "The deadline as mentioned in the text, e.g. 'end of day tomorrow', "
                                    "'Wednesday morning', 'Friday end of day'. "
                                    "Use 'UNKNOWN' if no deadline is mentioned."
                                )
                            },
                            "implies_completion": {
                                "type": "boolean",
                                "description": "True if the text clearly indicates this task has already been completed."
                            },
                            "excerpt": {
                                "type": "string",
                                "description": "The exact sentence(s) from the source that support this commitment."
                            }
                        },
                        "required": ["description", "owner", "ownership_confidence", "deadline", "implies_completion", "excerpt"]
                    }
                }
            },
            "required": ["commitments"]
        }
    }
}

SYSTEM_PROMPT = """You are extracting commitments, promises, and action items from executive business communications.

The executive context:
- Arjun Malhotra is VP Sales at Veridian Corp. He is the primary user.
- The week in question is 21–25 September 2026.
- Other people: Neha Kapoor (Marketing Lead), Raghav Sethi (Ops Manager), Divya Rao (Finance), Priya Nair (external client at Meridian Logistics), Facilities (internal distribution list).

Rules:
1. Extract ONLY commitments that are explicitly supported by the text. Do not invent or infer.
2. If ownership is disputed, unclear, or merely speculated (e.g. "I think it might be Facilities"), mark ownership_confidence as "suggested" or "unknown".
3. If Arjun says "flag it, don't assume" about something, mark owner as UNKNOWN and ownership_confidence as "unknown".
4. Deadline should be the exact phrasing from the text. Use "UNKNOWN" if not mentioned.
5. Mark implies_completion=true only if the text clearly states the task is done (e.g. "sent as promised", "confirmed, see you at 3").
6. The excerpt must be copied verbatim from the source text.
"""


class CommitmentExtractor:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncGroq(api_key=settings.groq_api_key, timeout=settings.groq_timeout)
        self._model = settings.groq_model

    async def extract_from_source(self, source: SourceDocument) -> list[tuple[dict[str, Any], Evidence]]:
        """
        Extract candidate commitments from a single SourceDocument.
        Returns list of (raw_extraction_dict, Evidence) pairs.
        """
        prompt = f"""Source type: {source.source_type.value}
Source date: {source.date}
Source label: {source.label}
Participants: {', '.join(source.participants) if source.participants else 'unknown'}

Text:
{source.raw_text}
"""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                tools=[EXTRACTION_TOOL],
                tool_choice={"type": "function", "function": {"name": "extract_commitments"}},
                temperature=0.1,
            )

            msg = response.choices[0].message
            if not msg.tool_calls:
                log.warning(f"No tool call from extractor for source {source.source_id}")
                return []

            args = json.loads(msg.tool_calls[0].function.arguments)
            raw_commitments = args.get("commitments", [])

            results = []
            for raw in raw_commitments:
                # Build an Evidence object for this extraction
                evidence = Evidence(
                    evidence_id=f"ev_{source.source_id}_{uuid.uuid4().hex[:6]}",
                    date=source.date,
                    time=source.time,
                    source=source,
                    speaker=_infer_speaker(raw.get("owner", ""), source),
                    excerpt=raw.get("excerpt", ""),
                    extracted_fact=raw.get("description", ""),
                    updates_deadline=False,  # Set by deadline_resolver later
                    implies_completion=raw.get("implies_completion", False),
                )
                results.append((raw, evidence))

            log.info(f"Extracted {len(results)} candidate commitments from {source.source_id}")
            return results

        except Exception as exc:
            log.error(f"Extraction failed for {source.source_id}: {exc!r}")
            return []

    async def extract_all(self, sources: list[SourceDocument]) -> list[tuple[dict[str, Any], Evidence]]:
        """Run extraction across all source documents sequentially."""
        all_candidates: list[tuple[dict[str, Any], Evidence]] = []
        for source in sources:
            candidates = await self.extract_from_source(source)
            all_candidates.extend(candidates)
        log.info(f"Total candidate commitments extracted: {len(all_candidates)}")
        return all_candidates


def _infer_speaker(owner: str, source: SourceDocument) -> str | None:
    """Best-guess the speaker based on owner field and source context."""
    if owner in KNOWN_PERSONS:
        return owner
    # For voice notes, speaker is always Arjun
    if source.source_type.value == "voice_note":
        return ARJUN
    return None
