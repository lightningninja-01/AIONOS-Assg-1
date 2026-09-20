"""
Source data loader.

Reads raw source files from data/sources/ and converts them
into normalized SourceDocument objects. These are the ONLY
objects that flow into the LLM extraction pipeline.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.models import SourceDocument, SourceType
from app.utils.logger import get_logger

log = get_logger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "sources"


def load_all_sources() -> list[SourceDocument]:
    """Load and return all SourceDocuments from the data pack."""
    sources: list[SourceDocument] = []
    sources.extend(_load_meeting_transcript())
    sources.extend(_load_voice_notes())
    sources.extend(_load_emails())
    log.info(f"Loaded {len(sources)} source documents from data pack")
    return sources


def _load_meeting_transcript() -> list[SourceDocument]:
    path = DATA_DIR / "meeting_transcript.txt"
    text = path.read_text(encoding="utf-8")
    return [
        SourceDocument(
            source_id="meeting_21sep",
            source_type=SourceType.meeting,
            date="2026-09-21",
            time="09:00",
            participants=["Arjun Malhotra", "Neha Kapoor", "Raghav Sethi", "Divya Rao"],
            raw_text=text,
            label="Leadership Sync — 21 Sep",
        )
    ]


def _load_voice_notes() -> list[SourceDocument]:
    path = DATA_DIR / "voice_notes.txt"
    full_text = path.read_text(encoding="utf-8")

    # Split on the separator between notes
    parts = full_text.split("---")
    # parts[0] = header/intro, parts[1] = voice note 1 section, parts[2] = voice note 2 section
    docs = []

    note_configs = [
        ("voice_note_1", "2026-09-21", "18:40", "Voice Note 1 — Arjun, 21 Sep (cab)"),
        ("voice_note_2", "2026-09-23", "08:15", "Voice Note 2 — Arjun, 23 Sep"),
    ]

    note_sections = [p.strip() for p in parts if p.strip() and "Voice Note" in p]
    for i, (section, (sid, date, time, label)) in enumerate(zip(note_sections, note_configs)):
        docs.append(
            SourceDocument(
                source_id=sid,
                source_type=SourceType.voice_note,
                date=date,
                time=time,
                participants=["Arjun Malhotra"],
                raw_text=section,
                label=label,
            )
        )

    return docs


def _load_emails() -> list[SourceDocument]:
    path = DATA_DIR / "emails.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    docs = []

    for thread in data["threads"]:
        thread_id = thread["thread_id"]
        subject = thread["subject"]
        for msg in thread["messages"]:
            body = msg["body"]
            participants = list({msg["from_name"], msg["to_name"]})
            raw_text = (
                f"Thread: {subject}\n"
                f"From: {msg['from_name']} <{msg['from']}>\n"
                f"To: {msg['to_name']} <{msg['to']}>\n"
                f"Date: {msg['date']} {msg['time']}\n\n"
                f"{body}"
            )
            docs.append(
                SourceDocument(
                    source_id=msg["message_id"],
                    source_type=SourceType.email,
                    date=msg["date"],
                    time=msg["time"],
                    participants=participants,
                    raw_text=raw_text,
                    label=f"Email — {subject} ({msg['date']} {msg['time']})",
                )
            )

    return docs
