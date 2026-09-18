"""
Security Orchestration Script: Run URL & Email heuristic checks across dataset_clean.json.
Extracts URLs and emails from full conversation texts, evaluates risk levels,
selects the highest-risk indicator per category, and saves output to security_flags.json.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure sybr root and backend/ are in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
BACKEND_DIR = SCRIPT_DIR / "backend"
if BACKEND_DIR.exists() and str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from security.url_check import check_url, extract_urls_from_text
    from security.email_check import check_email, extract_emails_from_text, parse_sender_header
except ImportError:
    from backend.security.url_check import check_url, extract_urls_from_text
    from backend.security.email_check import check_email, extract_emails_from_text, parse_sender_header

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run_security_checks")

# Numeric priority for risk comparison: High (3) > Medium (2) > Low (1)
RISK_PRIORITY = {
    "High": 3,
    "Medium": 2,
    "Low": 1,
}


def pick_highest_risk(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Selects the result dictionary with the highest risk level."""
    if not results:
        raise ValueError("Cannot pick highest risk from empty list")
    return max(results, key=lambda r: RISK_PRIORITY.get(r.get("risk", "Low"), 1))


def process_conversation(conv: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and analyzes all URLs and email addresses present in a conversation thread.
    Selects the highest-risk findings or sets safe defaults if none are detected.
    """
    conv_id = conv.get("conversation_id", "UNKNOWN")
    messages = conv.get("messages", [])

    # Collect full conversation text and sender headers
    text_segments: List[str] = []
    sender_entries: List[tuple[str, Optional[str]]] = []

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        # Message body
        raw_text = msg.get("text", "")
        if isinstance(raw_text, str) and raw_text.strip():
            text_segments.append(raw_text)

        # Clean text if available
        clean_text = msg.get("clean_text", "")
        if isinstance(clean_text, str) and clean_text.strip() and clean_text != raw_text:
            text_segments.append(clean_text)

        # Sender header (e.g. 'PayPal Resolution Center <support@paypa1-security.example>')
        sender = msg.get("sender", "")
        if isinstance(sender, str) and "@" in sender:
            text_segments.append(sender)
            parsed_email, parsed_display = parse_sender_header(sender)
            sender_entries.append((parsed_email, parsed_display))

    full_text = " \n ".join(text_segments)

    # 1. URL Analysis
    found_urls = extract_urls_from_text(full_text)
    if found_urls:
        url_evaluations = [check_url(u) for u in found_urls]
        top_url_res = pick_highest_risk(url_evaluations)
        url_risk = top_url_res["risk"]
        suspicious_url = url_risk in ("Medium", "High")
        url_reason = top_url_res["reason"]
    else:
        suspicious_url = False
        url_risk = "Low"
        url_reason = None

    # 2. Email Analysis
    # Combine emails found in text and explicitly parsed from senders
    found_emails = extract_emails_from_text(full_text)
    email_evaluations: List[Dict[str, Any]] = []

    # Map display names from senders if available
    display_map = {e.lower(): d for e, d in sender_entries if d}

    for e in found_emails:
        disp = display_map.get(e.lower())
        email_evaluations.append(check_email(e, display_name=disp))

    if email_evaluations:
        top_email_res = pick_highest_risk(email_evaluations)
        email_risk = top_email_res["risk"]
        suspicious_email = email_risk in ("Medium", "High")
        email_reason = top_email_res["reason"]
    else:
        suspicious_email = False
        email_risk = "Low"
        email_reason = None

    return {
        "conversation_id": conv_id,
        "suspicious_url": suspicious_url,
        "url_risk": url_risk,
        "url_reason": url_reason,
        "suspicious_email": suspicious_email,
        "email_risk": email_risk,
        "email_reason": email_reason,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # Locate dataset_clean.json
    search_paths = [
        Path("dataset_clean.json"),
        Path("backend/dataset_clean.json"),
        SCRIPT_DIR / "dataset_clean.json",
        BACKEND_DIR / "dataset_clean.json",
    ]
    dataset_file = next((p for p in search_paths if p.exists()), None)

    if not dataset_file:
        logger.error("dataset_clean.json not found. Please run preprocessing first.")
        sys.exit(1)

    logger.info("Loading cleaned dataset from %s ...", dataset_file)
    with open(dataset_file, "r", encoding="utf-8") as f:
        conversations = json.load(f)

    # Process all conversations
    security_records = [process_conversation(conv) for conv in conversations]

    # Calculate summary metrics
    total_conversations = len(security_records)
    flagged_urls = sum(1 for r in security_records if r["suspicious_url"])
    flagged_emails = sum(1 for r in security_records if r["suspicious_email"])

    # Save to security_flags.json in root and backend directories
    output_targets = [Path("security_flags.json")]
    if BACKEND_DIR.exists():
        output_targets.append(BACKEND_DIR / "security_flags.json")

    for target in output_targets:
        with open(target, "w", encoding="utf-8") as f:
            json.dump(security_records, f, indent=2, ensure_ascii=False)
        logger.info("Saved %d security flags records to %s", len(security_records), target)

    # Print summary statistics
    print("\n" + "=" * 75)
    print("                    SECURITY HEURISTICS RUN SUMMARY                   ")
    print("=" * 75)
    print(f"  Total conversations processed:      {total_conversations}")
    print(f"  Flagged suspicious_url (True):      {flagged_urls}")
    print(f"  Flagged suspicious_email (True):    {flagged_emails}")
    print("=" * 75 + "\n")

    # Manually print 8 sample results across real customer tickets and synthetic threats
    print("=" * 75)
    print("                 SAMPLE RESULTS SANITY-CHECK AUDIT                    ")
    print("=" * 75)

    # Separate real tickets from synthetic phish
    real_samples = [r for r in security_records if not r["conversation_id"].startswith("SYNTH")]
    synth_samples = [r for r in security_records if r["conversation_id"].startswith("SYNTH")]

    print("\n--- Real Customer Support Inquiries (Expected: Low Risk) ---")
    for r in real_samples[:5]:
        print(f"\n[ID: {r['conversation_id']}]")
        print(f"  URL Risk:   {r['url_risk']} | Suspicious: {r['suspicious_url']} | Reason: {r['url_reason']}")
        print(f"  Email Risk: {r['email_risk']} | Suspicious: {r['suspicious_email']} | Reason: {r['email_reason']}")

    print("\n--- Synthetic Social Engineering & Phishing (Expected: Medium/High Risk) ---")
    for r in synth_samples[:5]:
        print(f"\n[ID: {r['conversation_id']}]")
        print(f"  URL Risk:   {r['url_risk']} | Suspicious: {r['suspicious_url']} | Reason: {r['url_reason']}")
        print(f"  Email Risk: {r['email_risk']} | Suspicious: {r['suspicious_email']} | Reason: {r['email_reason']}")
    print("\n" + "=" * 75 + "\n")


if __name__ == "__main__":
    main()
