"""
F1. Flexible Ingestion and Dataset Normalization Engine.
Parses CSV and JSON data, automatically resolves varied column schemas, and groups multi-turn threads.
"""
import csv
import io
import json
import uuid
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from app.schemas import Message, AnalyzeRequest

# Canonical field aliases for flexible auto-mapping
COLUMN_ALIASES = {
    "text": [
        "text", "message", "body", "complaint", "description",
        "content", "issue", "query", "ticket_text", "comment", "utterance"
    ],
    "conversation_id": [
        "conversation_id", "ticket_id", "ticketid", "conv_id",
        "id", "thread_id", "ticket_number", "case_id", "session_id"
    ],
    "sender": [
        "sender", "role", "from", "author", "speaker", "user_type", "party"
    ],
    "timestamp": [
        "timestamp", "created_at", "date", "time", "sent_at", "datetime", "created_time"
    ],
    "channel": [
        "channel", "source", "medium", "platform", "entry_point", "type"
    ],
}


def detect_column_mapping(fieldnames: List[str]) -> Dict[str, Optional[str]]:
    """
    Auto-detects which dataset columns map to canonical fields:
    (text, conversation_id, sender, timestamp, channel).
    """
    mapping: Dict[str, Optional[str]] = {
        "text": None,
        "conversation_id": None,
        "sender": None,
        "timestamp": None,
        "channel": None,
    }

    lowered_fields = {f.strip().lower(): f for f in fieldnames}

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lowered_fields:
                mapping[canonical] = lowered_fields[alias]
                break

    return mapping


def parse_csv_content(csv_string: str) -> List[Dict[str, Any]]:
    """
    Parses a CSV string, maps its columns, and groups rows by conversation_id.
    Returns a list of conversation dictionaries ready for pipeline processing.
    """
    reader = csv.DictReader(io.StringIO(csv_string))
    if not reader.fieldnames:
        return []

    mapping = detect_column_mapping(reader.fieldnames)
    text_col = mapping["text"]
    if not text_col:
        raise ValueError(
            f"Could not find a text/message column in CSV. Found columns: {reader.fieldnames}"
        )

    id_col = mapping["conversation_id"]
    sender_col = mapping["sender"]
    time_col = mapping["timestamp"]
    channel_col = mapping["channel"]

    grouped_conversations: Dict[str, Dict[str, Any]] = {}
    row_counter = 1

    for row in reader:
        text_val = (row.get(text_col) or "").strip()
        if not text_val:
            continue

        # Determine conversation ID or generate sequential one
        conv_id = (row.get(id_col) or "").strip() if id_col else ""
        if not conv_id:
            conv_id = f"CS-{row_counter:05d}"
            row_counter += 1

        sender_val = (row.get(sender_col) or "").strip().lower() if sender_col else "customer"
        if not sender_val:
            sender_val = "customer"

        time_val = (row.get(time_col) or "").strip() if time_col else datetime.now(timezone.utc).isoformat()
        channel_val = (row.get(channel_col) or "").strip().lower() if channel_col else "ticket"
        if not channel_val:
            channel_val = "ticket"

        msg = Message(
            sender=sender_val,
            text=text_val,
            timestamp=time_val,
        )

        if conv_id not in grouped_conversations:
            grouped_conversations[conv_id] = {
                "conversation_id": conv_id,
                "channel": channel_val,
                "created_at": time_val,
                "messages": [msg],
                "source": "real",
            }
        else:
            grouped_conversations[conv_id]["messages"].append(msg)

    return list(grouped_conversations.values())


def parse_json_content(json_data: Any) -> List[Dict[str, Any]]:
    """
    Parses JSON data (list of objects, list of messages, or nested conversations structure).
    """
    raw_list: List[Dict[str, Any]] = []

    if isinstance(json_data, dict):
        if "conversations" in json_data and isinstance(json_data["conversations"], list):
            raw_list = json_data["conversations"]
        elif "tickets" in json_data and isinstance(json_data["tickets"], list):
            raw_list = json_data["tickets"]
        elif "messages" in json_data and isinstance(json_data["messages"], list):
            raw_list = json_data["messages"]
        else:
            raw_list = [json_data]
    elif isinstance(json_data, list):
        raw_list = json_data
    else:
        return []

    if not raw_list:
        return []

    # Check if first element already has nested 'messages' array
    sample = raw_list[0]
    if isinstance(sample, dict) and "messages" in sample and isinstance(sample["messages"], list):
        results = []
        for idx, item in enumerate(raw_list, start=1):
            conv_id = item.get("conversation_id") or item.get("id") or f"CS-{idx:05d}"
            channel = item.get("channel", "chat")
            created_at = item.get("created_at") or datetime.now(timezone.utc).isoformat()
            source = item.get("source", "real")

            msg_objs = []
            for m in item["messages"]:
                if isinstance(m, dict):
                    msg_objs.append(
                        Message(
                            sender=m.get("sender", "customer"),
                            text=m.get("text") or m.get("body") or m.get("message") or "",
                            timestamp=m.get("timestamp"),
                        )
                    )
                elif isinstance(m, str):
                    msg_objs.append(Message(sender="customer", text=m))

            results.append({
                "conversation_id": conv_id,
                "channel": channel,
                "created_at": created_at,
                "messages": msg_objs,
                "source": source,
            })
        return results

    # Otherwise treat elements as tabular rows
    sample_keys = list(sample.keys()) if isinstance(sample, dict) else []
    mapping = detect_column_mapping(sample_keys)
    text_col = mapping["text"] or "text"

    grouped: Dict[str, Dict[str, Any]] = {}
    row_counter = 1

    for row in raw_list:
        if not isinstance(row, dict):
            continue
        text_val = str(row.get(text_col) or "").strip()
        if not text_val:
            continue

        id_col = mapping["conversation_id"]
        conv_id = str(row.get(id_col) or "").strip() if id_col else ""
        if not conv_id:
            conv_id = f"CS-{row_counter:05d}"
            row_counter += 1

        sender_col = mapping["sender"]
        sender_val = str(row.get(sender_col) or "").strip().lower() if sender_col else "customer"

        time_col = mapping["timestamp"]
        time_val = str(row.get(time_col) or "").strip() if time_col else datetime.now(timezone.utc).isoformat()

        channel_col = mapping["channel"]
        channel_val = str(row.get(channel_col) or "").strip().lower() if channel_col else "chat"

        msg = Message(sender=sender_val, text=text_val, timestamp=time_val)

        if conv_id not in grouped:
            grouped[conv_id] = {
                "conversation_id": conv_id,
                "channel": channel_val,
                "created_at": time_val,
                "messages": [msg],
                "source": row.get("source", "real"),
            }
        else:
            grouped[conv_id]["messages"].append(msg)

    return list(grouped.values())


def normalize_analyze_request(req: AnalyzeRequest) -> Dict[str, Any]:
    """
    Normalizes a single /analyze request (which may provide single text or multi-turn messages).
    """
    conv_id = f"LIVE-{uuid.uuid4().hex[:8].upper()}"
    now_str = datetime.now(timezone.utc).isoformat()

    if req.messages:
        messages = req.messages
    elif req.text:
        messages = [Message(sender="customer", text=req.text, timestamp=now_str)]
    else:
        messages = [Message(sender="customer", text="", timestamp=now_str)]

    return {
        "conversation_id": conv_id,
        "user_id": req.user_id,
        "channel": req.channel or "chat",
        "created_at": now_str,
        "messages": messages,
        "source": req.source or "real",
        "urls": req.urls or [],
        "emails": req.emails or [],
        "attachments": req.attachments or [],
    }
