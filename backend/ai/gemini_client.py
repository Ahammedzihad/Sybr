"""
Gemini AI client integration module.
Configures Google Gemini API, provides analyze(), combined_intelligence(), summarize(),
and top-level process_conversation() with robust retry logic and partial-failure resilience.
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import dotenv
import google.generativeai as genai

# Add backend and root paths to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
ROOT_DIR = BACKEND_DIR.parent

for p in (str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Load .env from current directory and project roots
dotenv.load_dotenv()
dotenv.load_dotenv(BACKEND_DIR / ".env")
dotenv.load_dotenv(ROOT_DIR / ".env")

# Import shared PII masking utility
try:
    from utils import mask_pii
except ImportError:
    try:
        from backend.utils import mask_pii
    except ImportError:
        def mask_pii(text: str) -> str:
            """Pass-through fallback if utils module is not yet available."""
            return text if text else ""

# Get Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Configure genai with the key if available
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

DEFAULT_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.6-flash"]
FALLBACK_MODEL = "gemini-3.6-flash"


def get_model(model_name: str = DEFAULT_MODEL) -> genai.GenerativeModel:
    """Initialize a model using the specified model name (default: gemini-3.5-flash-lite)."""
    return genai.GenerativeModel(model_name)


def _clean_json_text(raw_text: str) -> str:
    """Strips Markdown code fences and extraneous whitespace from LLM response."""
    cleaned = (raw_text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()
    return cleaned


def _call_gemini_with_retry(prompt: str, model_name: str = DEFAULT_MODEL) -> str:
    """
    Executes a Gemini API call with retry logic:
    On rate-limit (429) or timeout/network error, waits 2 seconds and retries once
    before attempting fallback models or returning error.
    """
    models_to_try = [model_name] + [m for m in FALLBACK_MODELS if m != model_name]
    last_error = None

    for m_name in models_to_try:
        for attempt in range(2):  # 1 initial + 1 retry
            try:
                model = get_model(m_name)
                response = model.generate_content(prompt)
                raw_text = (response.text or "").strip()
                if raw_text:
                    return raw_text
            except Exception as err:
                last_error = err
                err_str = str(err).lower()
                is_retryable = any(k in err_str for k in ["429", "quota", "timeout", "deadline", "connection", "rate"])
                is_unavailable = any(k in err_str for k in ["404", "no longer available", "not found"])

                if is_unavailable:
                    break

                if is_retryable and attempt == 0:
                    time.sleep(2)  # wait 2 seconds and retry once
                    continue
                break

    if last_error:
        raise last_error
    return ""


def analyze(text: Optional[str], model_name: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """
    Analyzes customer support message using Gemini API.
    Masks PII prior to calling the API and returns structured JSON dictionary.
    """
    if text is None or not str(text).strip():
        return {
            "category": "Unknown",
            "sentiment": "Neutral",
            "emotion": "Neutral",
            "urgency": "Low",
            "priority": "Low",
            "keywords": [],
            "customer_request": "",
        }

    # Mask PII before sending outside local system
    masked_text = mask_pii(str(text))

    prompt = f"""You are a customer support intelligence system. Analyze the customer message below and return ONLY a valid JSON object, no markdown formatting, no explanation, no backticks.

Categories (pick exactly one): Billing/Payment, Account/Login, Delivery/Shipping, Technical Problem, Security Concern

Sentiment (pick exactly one): Positive, Neutral, Negative

Emotion (pick exactly one): Anger, Frustration, Confusion, Urgency, Disappointment, Satisfaction, Fear, Neutral

Priority (pick exactly one): Low, Medium, High, Critical
Priority = Critical if: account compromise, financial loss, fraud, legal threat, service outage, sensitive data exposure mentioned.
Priority = High if: repeated unresolved issue, strong negative emotion, money involved.

Keywords: extract 2-3 short key terms from the message (each keyword must be 1-3 words, not a full phrase).

Return exactly this JSON structure:
{{
  "category": "...",
  "sentiment": "...",
  "emotion": "...",
  "urgency": "Low|Medium|High",
  "priority": "...",
  "keywords": ["...", "..."],
  "customer_request": "one short sentence"
}}

CUSTOMER MESSAGE:
{masked_text}"""

    try:
        raw_text = _call_gemini_with_retry(prompt, model_name=model_name)
        cleaned_text = _clean_json_text(raw_text)

        try:
            parsed = json.loads(cleaned_text)
            if isinstance(parsed, dict):
                # Ensure keywords is a list of strings
                if "keywords" in parsed:
                    if isinstance(parsed["keywords"], list):
                        parsed["keywords"] = [str(k).strip() for k in parsed["keywords"] if str(k).strip()]
                    elif isinstance(parsed["keywords"], str):
                        parsed["keywords"] = [k.strip() for k in parsed["keywords"].split(",") if k.strip()]
                    else:
                        parsed["keywords"] = []
                return parsed
            return {"error": "parse_failed", "raw_response": raw_text}
        except (json.JSONDecodeError, ValueError):
            return {"error": "parse_failed", "raw_response": raw_text}

    except Exception as exc:
        return {"error": "api_failed", "reason": str(exc)}


def combined_intelligence(
    text: Optional[str],
    url_flag: Optional[Dict[str, Any]] = None,
    email_flag: Optional[Dict[str, Any]] = None,
    model_name: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """
    Combined customer-support and cybersecurity intelligence system.
    Determines customer intent, severity, social engineering tactics, and threat classification
    combining message text and pre-computed rule-based security signals.
    """
    if text is None or not str(text).strip():
        return {
            "threat_type": "None",
            "social_engineering": False,
            "technique": [],
            "risk_level": "Low",
            "recommended_action": "No action required.",
        }

    # Mask PII in the text prior to sending to external API
    masked_text = mask_pii(str(text))

    # Safely extract pre-computed security signals with defaults
    u_flag = url_flag if isinstance(url_flag, dict) else {}
    e_flag = email_flag if isinstance(email_flag, dict) else {}

    url_suspicious = u_flag.get("suspicious_url", False)
    url_risk = u_flag.get("risk", "Low")
    url_reason = u_flag.get("reason") if u_flag.get("reason") is not None else "None"

    email_suspicious = e_flag.get("suspicious_email", False)
    email_risk = e_flag.get("risk", "Low")
    email_reason = e_flag.get("reason") if e_flag.get("reason") is not None else "None"

    prompt = f"""You are a combined customer-support and cybersecurity intelligence system.
Given the customer message AND pre-computed security signals below, determine:
1. What the customer is saying and what they need
2. How serious the issue is
3. Whether this message represents a security threat

Security signals already detected (from rule-based analysis):
- Suspicious URL: {url_suspicious} (risk: {url_risk}, reason: {url_reason})
- Suspicious Email: {email_suspicious} (risk: {email_risk}, reason: {email_reason})

Social engineering techniques to check for (name any that apply): urgency, credential_harvesting, otp_request, impersonation

Return ONLY this JSON:
{{
  "threat_type": "None | Potential Phishing | Confirmed Phishing | Social Engineering",
  "social_engineering": true or false,
  "technique": ["urgency", "credential_harvesting"],
  "risk_level": "Low | Medium | High | Critical",
  "recommended_action": "one short actionable sentence"
}}

CUSTOMER MESSAGE:
{masked_text}"""

    try:
        raw_text = _call_gemini_with_retry(prompt, model_name=model_name)
        cleaned_text = _clean_json_text(raw_text)

        try:
            parsed = json.loads(cleaned_text)
            if isinstance(parsed, dict):
                # Ensure technique is a list of lowercase string identifiers
                if "technique" in parsed:
                    if isinstance(parsed["technique"], list):
                        parsed["technique"] = [str(t).strip() for t in parsed["technique"] if str(t).strip()]
                    elif isinstance(parsed["technique"], str):
                        parsed["technique"] = [t.strip() for t in parsed["technique"].split(",") if t.strip()]
                    else:
                        parsed["technique"] = []
                else:
                    parsed["technique"] = []

                if "social_engineering" in parsed:
                    parsed["social_engineering"] = bool(parsed["social_engineering"])

                return parsed
            return {"error": "parse_failed", "raw_response": raw_text}
        except (json.JSONDecodeError, ValueError):
            return {"error": "parse_failed", "raw_response": raw_text}

    except Exception as exc:
        return {"error": "api_failed", "reason": str(exc)}


def summarize(
    messages: Optional[List[Any]],
    model_name: str = DEFAULT_MODEL,
) -> Optional[Dict[str, Any]]:
    """
    Summarizes a multi-turn customer support conversation thread into a structured format.
    If len(messages) <= 1, returns None immediately to conserve API quota.
    """
    if not messages or len(messages) <= 1:
        return None

    # Format lines with speaker labels if available
    formatted_lines = []
    for msg in messages:
        if isinstance(msg, dict):
            sender = msg.get("sender") or msg.get("role") or msg.get("speaker") or "Customer"
            text = msg.get("text") or msg.get("message") or msg.get("content") or msg.get("body") or ""
            if text:
                formatted_lines.append(f"{str(sender).capitalize()}: {text}")
        elif isinstance(msg, str):
            if msg.strip():
                formatted_lines.append(msg.strip())
        else:
            formatted_lines.append(str(msg))

    if not formatted_lines or len(formatted_lines) <= 1:
        return None

    joined_text = "\n".join(formatted_lines)
    masked_text = mask_pii(joined_text)

    prompt = f"""Summarize this customer support conversation thread into a structured format.
Return ONLY this JSON:
{{
  "issue": "one sentence describing the core problem",
  "customer_request": "what the customer wants",
  "actions_taken": "what support has done so far",
  "current_status": "Resolved | Unresolved | Pending",
  "priority": "Low | Medium | High | Critical"
}}

CONVERSATION:
{masked_text}"""

    try:
        raw_text = _call_gemini_with_retry(prompt, model_name=model_name)
        cleaned_text = _clean_json_text(raw_text)

        try:
            parsed = json.loads(cleaned_text)
            if isinstance(parsed, dict):
                return parsed
            return {"error": "summarize_failed"}
        except (json.JSONDecodeError, ValueError):
            return {"error": "summarize_failed"}

    except Exception:
        return {"error": "summarize_failed"}


def process_conversation(
    text: Optional[str] = "",
    messages: Optional[List[Any]] = None,
    url_flag: Any = None,
    email_flag: Any = None,
    model_name: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """
    Top-level conversation intelligence and security threat processor:
    1. Calls analyze(text)
    2. Calls combined_intelligence(text, url_flag, email_flag)
    3. Calls summarize(messages) if len(messages) > 1, else sets summary to None
    4. Merges all three results into one dict using dictionary unpacking, with summary as a nested 'summary' key
    5. If any sub-call returned an 'error' key, sets 'partial_failure': True and preserves error details
    """
    msg_list = messages if isinstance(messages, list) else []

    # Handle fallback message joining if text is empty but messages are present
    effective_text = text or ""
    if not effective_text and msg_list:
        parts = []
        for m in msg_list:
            if isinstance(m, dict):
                parts.append(m.get("text") or m.get("message") or "")
            elif isinstance(m, str):
                parts.append(m)
        effective_text = " ".join([p for p in parts if p])

    # Normalization of url_flag and email_flag if booleans were passed
    if isinstance(url_flag, bool):
        url_flag_dict = {"suspicious_url": url_flag, "risk": "High" if url_flag else "Low", "reason": None}
    elif isinstance(url_flag, dict):
        url_flag_dict = url_flag
    else:
        url_flag_dict = {}

    if isinstance(email_flag, bool):
        email_flag_dict = {"suspicious_email": email_flag, "risk": "High" if email_flag else "Low", "reason": None}
    elif isinstance(email_flag, dict):
        email_flag_dict = email_flag
    else:
        email_flag_dict = {}

    # Step 1: analyze(text)
    analysis_res = analyze(effective_text, model_name=model_name)

    # Step 2: combined_intelligence(text, url_flag, email_flag)
    threat_res = combined_intelligence(effective_text, url_flag_dict, email_flag_dict, model_name=model_name)

    # Step 3: summarize(messages) if len(messages) > 1 else None
    if len(msg_list) > 1:
        summary_res = summarize(msg_list, model_name=model_name)
    else:
        summary_res = None

    # Step 4 & 5: Check for partial failures and merge
    errors: Dict[str, Any] = {}
    if isinstance(analysis_res, dict) and "error" in analysis_res:
        errors["analyze"] = analysis_res
    if isinstance(threat_res, dict) and "error" in threat_res:
        errors["combined_intelligence"] = threat_res
    if isinstance(summary_res, dict) and "error" in summary_res:
        errors["summarize"] = summary_res

    has_partial_failure = len(errors) > 0

    # Default fallback values for required schema fields
    merged: Dict[str, Any] = {
        "category": "Unknown",
        "sentiment": "Neutral",
        "emotion": "Neutral",
        "urgency": "Low",
        "priority": "Low",
        "keywords": [],
        "customer_request": effective_text[:120] if effective_text else "",
        "threat_type": "None",
        "social_engineering": False,
        "technique": [],
        "risk_level": "Low",
        "recommended_action": "Review conversation and verify details.",
    }

    # Merge analysis results (filtering error keys)
    if isinstance(analysis_res, dict):
        for k, v in analysis_res.items():
            if k not in ("error", "raw_response", "reason"):
                merged[k] = v

    # Merge threat results (filtering error keys)
    if isinstance(threat_res, dict):
        for k, v in threat_res.items():
            if k not in ("error", "raw_response", "reason"):
                merged[k] = v

    # Attach nested summary
    merged["summary"] = summary_res

    # Attach partial failure flag and error details
    if has_partial_failure:
        merged["partial_failure"] = True
        merged["errors"] = errors
    else:
        merged["partial_failure"] = False

    return merged


def test_hello_world(model_name: str = DEFAULT_MODEL) -> str:
    """
    Hello-world test function that sends 'Say hello' to Gemini and prints the response.
    """
    print(f"Sending 'Say hello' to Gemini model ({model_name})...")
    try:
        raw_text = _call_gemini_with_retry("Say hello", model_name=model_name)
        print(f"Response: {raw_text}")
        return raw_text
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        raise e


if __name__ == "__main__":
    test_hello_world()
