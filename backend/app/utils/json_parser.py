"""Robust JSON extraction and parsing for LLM outputs."""

import json
import re
from typing import Any, Dict, Optional
from app.core.logging import logger


def extract_and_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts and parses JSON from raw LLM output.
    Handles Markdown code blocks, leading/trailing prose, and minor formatting errors.
    """
    if not text:
        return None

    cleaned = text.strip()

    # Strip markdown fenced code blocks (e.g. ```json ... ``` or ``` ... ```)
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # Attempt direct JSON parse
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception as e:
        logger.debug(f"Direct JSON parse failed: {e}. Attempting regex extraction.")

    # Fallback: Extract outermost curly braces {...}
    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        extracted = match.group(1).strip()
        try:
            data = json.loads(extracted)
            if isinstance(data, dict):
                return data
        except Exception as e:
            logger.warning(f"Regex-extracted JSON parse failed: {e}")

    return None
