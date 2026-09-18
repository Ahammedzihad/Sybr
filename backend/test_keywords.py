"""
Test script to validate keyword extraction on real customer conversation datasets.
Runs analyze() on each message, calculates metrics, validates phrase lengths,
and saves validated results for handoff.
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Ensure backend and root directories are in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
for p in (str(CURRENT_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from ai.gemini_client import analyze
except ImportError:
    from backend.ai.gemini_client import analyze


def load_dataset() -> List[Dict[str, Any]]:
    """Loads customer conversation dataset from disk or fallback samples."""
    potential_paths = [
        CURRENT_DIR / "data" / "customer_conversations.json",
        ROOT_DIR / "data" / "customer_conversations.json",
        CURRENT_DIR / "customer_conversations.json",
    ]

    for p in potential_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    print(f"Loaded {len(data)} conversation records from: {p}", flush=True)
                    return data

    print("Falling back to default customer conversation samples.", flush=True)
    return [
        {"id": "MSG-01", "text": "I was double charged $49.99 on my credit card for this month's subscription. Please issue a refund immediately."},
        {"id": "MSG-02", "text": "My account has been locked after 3 failed login attempts. I am not receiving the password reset email."},
        {"id": "MSG-03", "text": "Tracking number TRK-99281 shows package delivered yesterday, but nothing arrived at my address."},
        {"id": "MSG-04", "text": "The dashboard API returns 500 Internal Server Error when exporting monthly CSV reports."},
        {"id": "MSG-05", "text": "We received an email claiming our domain DNS will expire unless we click a verification link. We suspect phishing."},
    ]


def run_keyword_analysis(dataset: List[Dict[str, Any]], max_retries: int = 4) -> Dict[str, Any]:
    """
    Executes analyze() across all dataset messages with rate limit resilience,
    collects keywords, and validates keyword lengths.
    """
    results = []
    failed_messages = []
    empty_keyword_messages = []
    overly_long_keyword_count = 0
    total_keyword_count = 0
    all_keywords_flat: List[str] = []
    keywords_per_message: List[List[str]] = []

    print(f"\nProcessing {len(dataset)} messages with analyze()...", flush=True)

    for i, item in enumerate(dataset, 1):
        msg_id = item.get("id", f"MSG-{i:03d}")
        text = item.get("text", "")
        print(f"[{i}/{len(dataset)}] Analyzing {msg_id}: '{text[:60]}...'", flush=True)

        res = None
        for attempt in range(max_retries):
            res = analyze(text)
            if "error" in res and "429" in str(res.get("reason", "")):
                reason = str(res.get("reason", ""))
                match = re.search(r"retry in (\d+(?:\.\d+)?)s", reason, re.IGNORECASE)
                if not match:
                    match = re.search(r"seconds:\s*(\d+)", reason)
                wait_time = (float(match.group(1)) + 2.0) if match else (20.0 + attempt * 10.0)
                print(f"    Rate limit hit (429). Waiting {wait_time:.1f}s for quota reset (attempt {attempt + 1}/{max_retries})...", flush=True)
                time.sleep(wait_time)
                continue
            break

        # Check for API / Parse failures
        if "error" in res:
            print(f"    FAILED: {res.get('error')} - {res.get('reason', res.get('raw_response', ''))}", flush=True)
            failed_messages.append({"id": msg_id, "text": text, "error": res})
            keywords = []
        else:
            raw_keywords = res.get("keywords", [])
            # Guarantee flat list of strings
            if isinstance(raw_keywords, list):
                keywords = [str(k).strip() for k in raw_keywords if str(k).strip()]
            elif isinstance(raw_keywords, str):
                keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()]
            else:
                keywords = []

        if not keywords:
            empty_keyword_messages.append({"id": msg_id, "text": text})

        # Check for overly long keyword phrases (> 4 words)
        for kw in keywords:
            word_count = len(kw.split())
            if word_count > 4:
                overly_long_keyword_count += 1
                print(f"    Notice: Overly long keyword ({word_count} words): '{kw}'", flush=True)

        print(f"    Keywords: {keywords}", flush=True)
        total_keyword_count += len(keywords)
        all_keywords_flat.extend(keywords)
        keywords_per_message.append(keywords)

        results.append({
            "id": msg_id,
            "text": text,
            "category": res.get("category", "Unknown"),
            "sentiment": res.get("sentiment", "Unknown"),
            "priority": res.get("priority", "Unknown"),
            "keywords": keywords,
        })

        # Pacing between requests
        if i < len(dataset):
            time.sleep(2)

    total_messages = len(dataset)
    avg_keywords = (total_keyword_count / total_messages) if total_messages > 0 else 0.0
    long_keyword_percentage = (overly_long_keyword_count / total_keyword_count * 100) if total_keyword_count > 0 else 0.0

    summary = {
        "total_messages_processed": total_messages,
        "total_keywords_extracted": total_keyword_count,
        "average_keywords_per_message": round(avg_keywords, 2),
        "empty_keyword_messages_count": len(empty_keyword_messages),
        "empty_keyword_messages": empty_keyword_messages,
        "failed_api_calls_count": len(failed_messages),
        "failed_api_calls": failed_messages,
        "overly_long_keywords_count": overly_long_keyword_count,
        "overly_long_keywords_percentage": round(long_keyword_percentage, 2),
        "keywords_per_message": keywords_per_message,
        "all_keywords_flat": all_keywords_flat,
        "detailed_results": results,
    }

    return summary


def print_summary(summary: Dict[str, Any]) -> None:
    """Prints a clear terminal summary of the keyword extraction evaluation."""
    print("\n" + "=" * 60, flush=True)
    print("KEYWORD EXTRACTION EVALUATION SUMMARY", flush=True)
    print("=" * 60, flush=True)
    print(f"Total Messages Processed:           {summary['total_messages_processed']}", flush=True)
    print(f"Total Keywords Extracted:           {summary['total_keywords_extracted']}", flush=True)
    print(f"Average Keywords per Message:       {summary['average_keywords_per_message']}", flush=True)
    print(f"Empty Keywords Count:               {summary['empty_keyword_messages_count']}", flush=True)
    print(f"Failed API Calls Count:             {summary['failed_api_calls_count']}", flush=True)
    print(f"Overly Long Keywords (>4 words):    {summary['overly_long_keywords_count']} ({summary['overly_long_keywords_percentage']}%)", flush=True)
    print("=" * 60, flush=True)

    if summary["empty_keyword_messages"]:
        print("\nMessages with Empty Keywords:", flush=True)
        for item in summary["empty_keyword_messages"]:
            print(f"  - [{item['id']}]: {item['text']}", flush=True)

    if summary["failed_api_calls"]:
        print("\nFailed API Calls:", flush=True)
        for item in summary["failed_api_calls"]:
            print(f"  - [{item['id']}]: {item.get('error')}", flush=True)

    if summary["overly_long_keywords_percentage"] > 20.0:
        print("\n[WARNING] Over 20% of keywords are overly long phrases! Tightening prompt required.", flush=True)
    else:
        print("\n[PASS] Keyword brevity criteria satisfied (< 20% long phrases).", flush=True)


def save_handoff_results(summary: Dict[str, Any]) -> None:
    """Saves the validated keyword extraction results to JSON files for handoff."""
    handoff_payload = {
        "metadata": {
            "total_messages": summary["total_messages_processed"],
            "total_keywords": summary["total_keywords_extracted"],
            "average_keywords_per_message": summary["average_keywords_per_message"],
            "overly_long_keywords_percentage": summary["overly_long_keywords_percentage"],
        },
        "flat_keywords_per_message": summary["keywords_per_message"],
        "all_keywords_flat": summary["all_keywords_flat"],
        "records": summary["detailed_results"],
    }

    output_paths = [
        CURRENT_DIR / "data" / "extracted_keywords.json",
        ROOT_DIR / "extracted_keywords.json",
    ]

    for out_path in output_paths:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(handoff_payload, f, indent=2)
        print(f"Saved handoff keyword extraction results to: {out_path}", flush=True)


def main():
    dataset = load_dataset()
    summary = run_keyword_analysis(dataset)
    print_summary(summary)
    save_handoff_results(summary)


if __name__ == "__main__":
    main()
