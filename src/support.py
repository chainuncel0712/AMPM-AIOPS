"""Support FAQ — lightweight keyword-based Q&A for support group."""

import json
import re
from pathlib import Path

FAQ_FILE = Path(__file__).parent.parent / "data" / "faq.json"


def _load():
    if FAQ_FILE.exists():
        try:
            return json.loads(FAQ_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def find_answer(text: str) -> str | None:
    """Search FAQ by keyword match. Returns answer string or None."""
    faq = _load()
    text_lower = text.lower()
    for item in faq:
        for kw in item["keywords"]:
            if kw.lower() in text_lower:
                return item["answer"]
    return None


def auto_reply(text: str) -> str | None:
    """Group support auto-reply. Returns reply or None if no match."""
    # Check for help keywords
    help_triggers = ["help", "幫助", "怎麼", "如何", "問題", "請問", "客服", "support"]
    if not any(t in text.lower() for t in help_triggers):
        return None
    return find_answer(text)
