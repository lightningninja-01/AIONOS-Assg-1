"""
Date normalizer.

Converts relative date expressions ("tomorrow", "Wednesday morning",
"end of day") into ISO 8601 datetime strings, anchored to the known
week: Mon 21 Sep – Fri 25 Sep 2026.
"""
from __future__ import annotations

import re

WEEK = {
    "monday": "2026-09-21",
    "tuesday": "2026-09-22",
    "wednesday": "2026-09-23",
    "thursday": "2026-09-24",
    "friday": "2026-09-25",
    "mon": "2026-09-21",
    "tue": "2026-09-22",
    "wed": "2026-09-23",
    "thu": "2026-09-24",
    "fri": "2026-09-25",
}

DAY_FROM_DATE = {v: k for k, v in WEEK.items() if len(k) > 3}

SOURCE_DATE_TO_TOMORROW = {
    "2026-09-21": "2026-09-22",
    "2026-09-22": "2026-09-23",
    "2026-09-23": "2026-09-24",
    "2026-09-24": "2026-09-25",
}


def normalize_deadline(text: str, source_date: str) -> tuple[str | None, str]:
    """
    Returns (iso_datetime_str | None, human_label).

    iso_datetime_str: "2026-09-23T09:00:00" or None if genuinely unknown.
    human_label: cleaned human-readable deadline label.
    """
    t = text.strip().lower()

    if not t or t in ("unknown", "none", "n/a", ""):
        return None, "UNKNOWN"

    # Explicit ISO already
    if re.match(r"\d{4}-\d{2}-\d{2}", t):
        return t if "T" in t else t + "T00:00:00", text

    # "today"
    if "today" in t:
        time = _extract_time(t)
        return f"{source_date}T{time}", f"Today ({source_date}) {_friendly_time(time)}"

    # "tomorrow"
    if "tomorrow" in t:
        next_day = SOURCE_DATE_TO_TOMORROW.get(source_date, source_date)
        time = _extract_time(t)
        return f"{next_day}T{time}", f"Tomorrow ({next_day}) {_friendly_time(time)}"

    # Named day
    for day_name, day_date in WEEK.items():
        if day_name in t:
            time = _extract_time(t)
            label_day = day_name.capitalize()
            return f"{day_date}T{time}", f"{label_day} ({day_date}) {_friendly_time(time)}"

    # "end of day" / "EOD"
    if "end of day" in t or "eod" in t:
        return f"{source_date}T17:00:00", f"End of day {source_date}"

    # "this week"
    if "this week" in t or "week" in t:
        return "2026-09-25T17:00:00", "This week (by Friday)"

    # "ASAP" or "as soon as possible"
    if "asap" in t or "as soon as" in t:
        return f"{source_date}T23:59:00", "ASAP"

    return None, text  # Return original text as label if we can't parse


def _extract_time(text: str) -> str:
    """Extract a time string from the text, defaulting sensibly."""
    if "morning" in text:
        return "09:00:00"
    if "evening" in text or "end of day" in text or "eod" in text:
        return "18:00:00"
    if "afternoon" in text:
        return "14:00:00"
    if "night" in text:
        return "20:00:00"
    # Check for explicit time like "3:00 PM" or "9:30 AM"
    m = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)?", text, re.IGNORECASE)
    if m:
        h, minute, meridian = int(m.group(1)), m.group(2), m.group(3) or ""
        if meridian.lower() == "pm" and h != 12:
            h += 12
        elif meridian.lower() == "am" and h == 12:
            h = 0
        return f"{h:02d}:{minute}:00"
    return "09:00:00"  # default: start of business day


def _friendly_time(time_str: str) -> str:
    if time_str == "09:00:00":
        return "morning"
    if time_str == "18:00:00":
        return "evening"
    if time_str == "17:00:00":
        return "end of day"
    return time_str[:5]
