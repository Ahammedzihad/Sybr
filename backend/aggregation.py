"""
Aggregation utilities for customer conversations and intelligence analytics.
"""

import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    import storage
except ImportError:
    from backend import storage

RESOLUTION_KEYWORDS = [
    "resolved",
    "refunded",
    "fixed",
    "completed",
    "thank you",
    "issue closed",
    "confirmed",
]

UNRESOLVED_SIGNALS = [
    "still",
    "haven't",
    "not yet",
    "again",
    "still waiting",
    "no response",
]


def detect_resolution(messages: List[str]) -> str:
    """
    Infers conversation resolution status based on keyword signals across messages.

    - If messages list is empty, return "Unknown" immediately.
    - Join all messages into lowercase full_text.
    - Get the last message in the list as last_customer_msg (lowercase).
    - If full_text contains any RESOLUTION_KEYWORDS and last_customer_msg doesn't contain
      any UNRESOLVED_SIGNALS, return "Resolved".
    - Else if last_customer_msg contains any UNRESOLVED_SIGNALS, return "Unresolved".
    - Else return "Pending".
    """
    if not messages:
        return "Unknown"

    # Safely convert to strings and ignore empty entries if any
    raw_list = []
    for m in messages:
        if isinstance(m, dict):
            raw_list.append(str(m.get("text") or m.get("message") or m.get("content") or m.get("body") or ""))
        elif m is not None:
            raw_list.append(str(m))

    if not raw_list:
        return "Unknown"

    full_text = " ".join(raw_list).lower()
    last_customer_msg = raw_list[-1].lower()

    has_resolution = any(kw in full_text for kw in RESOLUTION_KEYWORDS)
    has_unresolved_signal = any(sig in last_customer_msg for sig in UNRESOLVED_SIGNALS)

    if has_resolution and not has_unresolved_signal:
        return "Resolved"
    elif has_unresolved_signal:
        return "Unresolved"
    else:
        return "Pending"


def frequently_reported_issues() -> Dict[str, List[Tuple[str, int]]]:
    """
    Analyzes all conversation records from storage and calculates:
    - Frequencies of each category (skipping missing or 'Unknown' categories).
    - Frequencies of keywords across all records (top 10, skipping empty/missing).

    Returns:
        Dict containing:
            "by_category": List[Tuple[str, int]] of categories ordered by frequency
            "by_keyword": List[Tuple[str, int]] of top 10 keywords ordered by frequency
    """
    records = storage.get_all()
    category_counts: Counter = Counter()
    keyword_counts: Counter = Counter()

    for record in records:
        if not isinstance(record, dict):
            continue

        # 1. Count category (skip missing, empty, or 'Unknown')
        category = record.get("category")
        if category and isinstance(category, str):
            category_clean = category.strip()
            if category_clean and category_clean.lower() != "unknown":
                category_counts[category_clean] += 1

        # 2. Count keywords (flatten list, skip missing/empty)
        keywords = record.get("keywords")
        if isinstance(keywords, list):
            for kw in keywords:
                if kw is not None:
                    kw_str = str(kw).strip()
                    if kw_str:
                        keyword_counts[kw_str] += 1
        elif isinstance(keywords, str):
            kw_str = keywords.strip()
            if kw_str:
                keyword_counts[kw_str] += 1

    return {
        "by_category": category_counts.most_common(),
        "by_keyword": keyword_counts.most_common(10),
    }
