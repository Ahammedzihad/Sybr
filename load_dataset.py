"""
Data Ingestion and Normalization Script for Customer Support & Phishing Detection.
Loads raw real customer support data, normalizes into uniform schema,
logs skipping of missing/empty rows, generates summary statistics,
synthesizes varied social engineering & phishing attacks, and outputs:
- dataset_normalized.json (real data only)
- dataset.json (real + synthetic threats combined)
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("load_dataset")


# Candidate column name variations for automatic schema adaptation
ID_CANDIDATES = ["conversation_id", "convo_id", "ticket_id", "ticket_num", "id", "thread_id", "issue_id", "ticket"]
SENDER_CANDIDATES = ["sender", "speaker", "speaker_role", "role", "author", "from", "actor", "user_type"]
TEXT_CANDIDATES = ["text", "message", "message_body", "message_content", "body", "utterance", "content", "dialogue", "comment"]
TIMESTAMP_CANDIDATES = ["timestamp", "timestamp_utc", "created_at", "created_date", "time", "date", "datetime"]


def find_column(headers: List[str], candidates: List[str]) -> Optional[str]:
    """Find matching column name case-insensitively from candidate list."""
    lookup = {h.lower().strip(): h for h in headers}
    for c in candidates:
        if c.lower() in lookup:
            return lookup[c.lower()]
    return None


def detect_file_structure(file_path: Path) -> Tuple[str, Dict[str, Optional[str]]]:
    """Inspect CSV/JSON file to detect field mappings and format."""
    ext = file_path.suffix.lower()
    if ext == ".csv":
        with open(file_path, mode="r", encoding="utf-8", errors="replace") as f:
            sample = f.read(4096)
            f.seek(0)
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(sample)
                has_header = sniffer.has_header(sample)
            except csv.Error:
                dialect = csv.excel
                has_header = True

            reader = csv.reader(f, dialect)
            first_row = next(reader, [])
            matched_candidates = [
                find_column(first_row, ID_CANDIDATES),
                find_column(first_row, SENDER_CANDIDATES),
                find_column(first_row, TEXT_CANDIDATES),
                find_column(first_row, TIMESTAMP_CANDIDATES),
            ]
            if any(matched_candidates) or has_header:
                headers = first_row
            else:
                headers = []

        col_map = {
            "id": find_column(headers, ID_CANDIDATES),
            "sender": find_column(headers, SENDER_CANDIDATES),
            "text": find_column(headers, TEXT_CANDIDATES),
            "timestamp": find_column(headers, TIMESTAMP_CANDIDATES),
        }
        logger.info("Detected CSV columns -> ID: %s, Sender: %s, Text: %s, Timestamp: %s",
                    col_map["id"], col_map["sender"], col_map["text"], col_map["timestamp"])
        return "csv", col_map

    elif ext == ".json":
        with open(file_path, mode="r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        if isinstance(data, list) and len(data) > 0:
            sample = data[0]
            if isinstance(sample, dict):
                headers = list(sample.keys())
                col_map = {
                    "id": find_column(headers, ID_CANDIDATES),
                    "sender": find_column(headers, SENDER_CANDIDATES),
                    "text": find_column(headers, TEXT_CANDIDATES),
                    "timestamp": find_column(headers, TIMESTAMP_CANDIDATES),
                }
                logger.info("Detected JSON fields -> ID: %s, Sender: %s, Text: %s, Timestamp: %s",
                            col_map["id"], col_map["sender"], col_map["text"], col_map["timestamp"])
                return "json_records", col_map
        return "json_normalized", {}
    else:
        raise ValueError(f"Unsupported file format: {file_path.name}")


def load_real_dataset(file_path: Path) -> Tuple[List[Dict[str, Any]], int]:
    """
    Loads and normalizes real dataset into list of conversation objects.
    Returns (conversations, skipped_count).
    """
    fmt, col_map = detect_file_structure(file_path)
    skipped_count = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    if fmt == "csv":
        conversations_dict: Dict[str, Dict[str, Any]] = {}
        with open(file_path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=1):
                raw_text = row.get(col_map["text"] or "", "") if col_map["text"] else ""
                
                # Check for null / empty text
                if not raw_text or not raw_text.strip():
                    skipped_count += 1
                    logger.warning("Row %d: Skipped due to missing or empty message text.", row_idx)
                    continue

                raw_id = (row.get(col_map["id"] or "") or "").strip() if col_map["id"] else ""
                if not raw_id:
                    # Generate fallback clean unique identifier
                    conv_id = f"CS-{row_idx:05d}"
                    logger.info("Row %d: Missing conversation_id, auto-generated '%s'", row_idx, conv_id)
                else:
                    conv_id = raw_id

                sender = (row.get(col_map["sender"] or "") or "").strip() if col_map["sender"] else "customer"
                if not sender:
                    sender = "customer"

                ts = (row.get(col_map["timestamp"] or "") or "").strip() if col_map["timestamp"] else now_iso
                if not ts:
                    ts = now_iso

                message = {
                    "sender": sender,
                    "text": raw_text.strip(),
                    "timestamp": ts,
                }

                if conv_id not in conversations_dict:
                    conversations_dict[conv_id] = {
                        "conversation_id": conv_id,
                        "messages": [],
                    }
                conversations_dict[conv_id]["messages"].append(message)

        return list(conversations_dict.values()), skipped_count

    elif fmt == "json_records":
        with open(file_path, mode="r", encoding="utf-8", errors="replace") as f:
            records = json.load(f)

        conversations_dict = {}
        for row_idx, item in enumerate(records, start=1):
            raw_text = item.get(col_map["text"] or "", "") if col_map["text"] else ""
            if not raw_text or not str(raw_text).strip():
                skipped_count += 1
                logger.warning("Item %d: Skipped due to missing/empty message text.", row_idx)
                continue

            raw_id = str(item.get(col_map["id"] or "") or "").strip() if col_map["id"] else ""
            conv_id = raw_id if raw_id else f"CS-{row_idx:05d}"
            sender = str(item.get(col_map["sender"] or "") or "customer").strip() or "customer"
            ts = str(item.get(col_map["timestamp"] or "") or now_iso).strip() or now_iso

            msg = {
                "sender": sender,
                "text": str(raw_text).strip(),
                "timestamp": ts,
            }
            if conv_id not in conversations_dict:
                conversations_dict[conv_id] = {
                    "conversation_id": conv_id,
                    "messages": [],
                }
            conversations_dict[conv_id]["messages"].append(msg)

        return list(conversations_dict.values()), skipped_count

    else:
        # Already normalized JSON structure
        with open(file_path, mode="r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        conversations = []
        for row_idx, conv in enumerate(data, start=1):
            conv_id = conv.get("conversation_id") or f"CS-{row_idx:05d}"
            msgs = []
            for msg in conv.get("messages", []):
                txt = msg.get("text", "")
                if not txt or not str(txt).strip():
                    skipped_count += 1
                    continue
                msgs.append({
                    "sender": msg.get("sender", "customer"),
                    "text": str(txt).strip(),
                    "timestamp": msg.get("timestamp", now_iso),
                })
            if msgs:
                conversations.append({"conversation_id": conv_id, "messages": msgs})
            else:
                skipped_count += 1
        return conversations, skipped_count


def generate_synthetic_threats() -> List[Dict[str, Any]]:
    """
    Hand-crafted synthetic phishing and social-engineering conversations.
    Techniques represented:
    - 3 Urgency ("act now", "within 24 hours", "account will be suspended")
    - 3 Credential Harvesting ("enter your password", "confirm your login")
    - 2 OTP Request ("share the OTP sent to your phone")
    - 2 Impersonation (fake lookalike domain 'paypa1-security.example', spoofed display name)
    """
    ts = datetime.now(timezone.utc).isoformat()
    return [
        # 1. Urgency: 24-hour suspension with IP literal URL
        {
            "conversation_id": "SYNTH-PHISH-01",
            "messages": [
                {
                    "sender": "attacker",
                    "text": "FINAL NOTICE: Your billing profile failed automated re-verification. Act now within 24 hours or your cloud account will be suspended and all stored data terminated permanently. Verify immediately at http://192.168.1.105/auth-renew.",
                    "timestamp": ts,
                }
            ],
            "threat_meta": {
                "technique": "Urgency",
                "target": "Account Suspension",
                "indicator": "within 24 hours, act now, IP URL",
            }
        },
        # 2. Urgency: Immediate freeze / 2-hour window with URL shortener
        {
            "conversation_id": "SYNTH-PHISH-02",
            "messages": [
                {
                    "sender": "attacker",
                    "text": "SECURITY ALERT: We observed suspicious login attempts from Moscow, Russia. Your account will be suspended within 2 hours unless you act now to confirm your active device identity.",
                    "timestamp": ts,
                },
                {
                    "sender": "customer",
                    "text": "Wait, I didn't authorize any login from Russia! How do I stop this?",
                    "timestamp": ts,
                },
                {
                    "sender": "attacker",
                    "text": "Act now: Click our emergency cancellation link http://tinyurl.com/urgent-verify-device before your session expires.",
                    "timestamp": ts,
                }
            ],
            "threat_meta": {
                "technique": "Urgency",
                "target": "Session Freeze",
                "indicator": "suspended within 2 hours, act now, shortener URL",
            }
        },
        # 3. Urgency: Immediate payment cancellation with lookalike email & shortener URL
        {
            "conversation_id": "SYNTH-PHISH-03",
            "messages": [
                {
                    "sender": "Stripe Billing Notifications <billing-support@str1pe-billing.example>",
                    "text": "Your recent enterprise subscription charge of $4,850 could not be processed. Act now to prevent service interruption—your entire company account will be suspended tomorrow at 08:00 UTC without immediate payment settlement. Review invoice and settle at http://bit.ly/stripe-dispute-settle or contact billing-support@str1pe-billing.example.",
                    "timestamp": ts,
                }
            ],
            "threat_meta": {
                "technique": "Urgency",
                "target": "Payment Termination",
                "indicator": "account will be suspended tomorrow, act now, shortener link, lookalike email",
            }
        },
        # 4. Credential Harvesting: Long unencrypted HTTP password confirmation
        {
            "conversation_id": "SYNTH-PHISH-04",
            "messages": [
                {
                    "sender": "attacker",
                    "text": "To restore full access to your support ticketing portal, please enter your password and registered email address to verify ownership: http://secure-sso-gateway.example/login-portal-auth-credential-recovery-token-verification-session-id-9982412",
                    "timestamp": ts,
                }
            ],
            "threat_meta": {
                "technique": "Credential Harvesting",
                "target": "SSO Password",
                "indicator": "enter your password, confirm your login, long unencrypted URL",
            }
        },
        # 5. Credential Harvesting: Re-authentication form with private/local IP URL
        {
            "conversation_id": "SYNTH-PHISH-05",
            "messages": [
                {
                    "sender": "attacker",
                    "text": "Our IT administrator recently applied updated zero-trust policies. You must confirm your login immediately. Please enter your password and current master PIN on our secure verification portal at http://10.14.8.99/auth-verify to continue using internal chat.",
                    "timestamp": ts,
                }
            ],
            "threat_meta": {
                "technique": "Credential Harvesting",
                "target": "Master PIN / Password",
                "indicator": "confirm your login, enter your password, IP literal URL",
            }
        },
        # 6. Credential Harvesting: In-chat credential request with spoofed internal lookalike email
        {
            "conversation_id": "SYNTH-PHISH-06",
            "messages": [
                {
                    "sender": "customer",
                    "text": "I am having trouble downloading my sales tax reports.",
                    "timestamp": ts,
                },
                {
                    "sender": "Internal Helpdesk <support@slck-internal.example>",
                    "text": "I am an elevated technical agent. To run diagnostics on your database container, please reply here or contact sysadmin@slck-internal.example and enter your password and admin username directly in this thread so I can reproduce the error.",
                    "timestamp": ts,
                }
            ],
            "threat_meta": {
                "technique": "Credential Harvesting",
                "target": "Admin Credentials in-chat",
                "indicator": "enter your password directly, lookalike sender domain",
            }
        },
        # 7. OTP Request: Refund authorization with brand typosquat URL
        {
            "conversation_id": "SYNTH-PHISH-07",
            "messages": [
                {
                    "sender": "customer",
                    "text": "Can you check why ₹2,500 was deducted without confirmation?",
                    "timestamp": ts,
                },
                {
                    "sender": "attacker",
                    "text": "I have processed your immediate reversal of ₹2,500. A 6-digit verification code has been triggered to your mobile number. Please share the OTP sent to your phone or confirm identity at http://paypa1-support.example/otp-auth so I can authorize the instant deposit back to your UPI account.",
                    "timestamp": ts,
                }
            ],
            "threat_meta": {
                "technique": "OTP Request",
                "target": "Banking/2FA OTP",
                "indicator": "share the OTP sent to your phone, lookalike URL",
            }
        },
        # 8. OTP Request: Account unlock verification with Amazon lookalike sender & URL
        {
            "conversation_id": "SYNTH-PHISH-08",
            "messages": [
                {
                    "sender": "Account Security Dispatch <security-alerts@amaz0n-security.example>",
                    "text": "Customer Support Dispatch: Your security profile requires two-step SMS verification. We just sent an SMS code to your registered mobile device ending in 4109. Please share the OTP sent to your phone with this agent or verify at https://amaz0n-security.example/sms-confirm to validate and unlock your profile.",
                    "timestamp": ts,
                }
            ],
            "threat_meta": {
                "technique": "OTP Request",
                "target": "2FA Bypass",
                "indicator": "share the OTP sent to your phone, lookalike domain amaz0n",
            }
        },
        # 9. Impersonation: Lookalike domain paypa1-security.example
        {
            "conversation_id": "SYNTH-PHISH-09",
            "messages": [
                {
                    "sender": "PayPal Resolution Center <support@paypa1-security.example>",
                    "text": "Dear customer, a dispute has been opened for unauthorized transaction #PP-8491 ($840.00 USD). If you did not make this purchase, review the transaction immediately at https://paypa1-security.example/disputes/cancel before funds clear.",
                    "timestamp": ts,
                }
            ],
            "threat_meta": {
                "technique": "Impersonation",
                "target": "Brand Impersonation / Typosquatting",
                "indicator": "lookalike domain paypa1-security.example, spoofed display name",
            }
        },
        # 10. Impersonation: Microsoft lookalike domain & spoofed display name
        {
            "conversation_id": "SYNTH-PHISH-10",
            "messages": [
                {
                    "sender": "Microsoft 365 Admin Center <admin-alerts@micros0ft-verify.example>",
                    "text": "Security bulletin MS-991: Unauthorized tenant access detected. Your administrator mailbox has been quarantined. Validate your tenant credentials at http://micros0ft-verify.example/tenant-login to restore normal email exchange routing.",
                    "timestamp": ts,
                }
            ],
            "threat_meta": {
                "technique": "Impersonation",
                "target": "Enterprise Brand Spoofing",
                "indicator": "lookalike domain micros0ft-verify.example, spoofed display name",
            }
        },
    ]


def main():
    parser = argparse.ArgumentParser(description="Normalize dataset and synthesize phishing messages")
    parser.add_argument("--input", default="customer_support_raw.csv", help="Input raw CSV or JSON file")
    parser.add_argument("--output-normalized", default="dataset_normalized.json", help="Path for normalized real dataset")
    parser.add_argument("--output-combined", default="dataset.json", help="Path for combined real + synthetic dataset")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        # Fallback to local directory if relative
        alt = Path(__file__).resolve().parent / args.input
        if alt.exists():
            input_path = alt
        else:
            logger.error("Could not find input file: %s", args.input)
            sys.exit(1)

    logger.info("Loading dataset from %s ...", input_path)
    real_conversations, skipped_count = load_real_dataset(input_path)

    total_conversations = len(real_conversations)
    total_messages = sum(len(c["messages"]) for c in real_conversations)
    avg_msgs = (total_messages / total_conversations) if total_conversations > 0 else 0.0

    # Print required summary statistics
    print("\n" + "=" * 60)
    print("           DATASET INGESTION & NORMALIZATION SUMMARY        ")
    print("=" * 60)
    print(f"  Total conversations loaded:       {total_conversations}")
    print(f"  Total skipped due to missing/empty: {skipped_count}")
    print(f"  Total valid messages loaded:       {total_messages}")
    print(f"  Average messages per conversation: {avg_msgs:.2f}")
    print("=" * 60 + "\n")

    # Save dataset_normalized.json (real data only)
    out_norm = Path(args.output_normalized)
    with open(out_norm, "w", encoding="utf-8") as f:
        json.dump(real_conversations, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d normalized real conversations to %s", len(real_conversations), out_norm)

    # Generate synthetic threats
    synthetic_threats = generate_synthetic_threats()
    logger.info("Generated %d synthetic phishing / social engineering entries.", len(synthetic_threats))

    # Save dataset.json (real + synthetic combined)
    combined_dataset = real_conversations + synthetic_threats
    out_comb = Path(args.output_combined)
    with open(out_comb, "w", encoding="utf-8") as f:
        json.dump(combined_dataset, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d combined conversations (real + synthetic) to %s", len(combined_dataset), out_comb)


if __name__ == "__main__":
    main()
