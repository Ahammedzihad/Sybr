"""
URL security check module.
Stub implementation returning safe placeholder results.
"""

from typing import Any, Dict


def check_url(url: str) -> Dict[str, Any]:
    """Stub function to check URL risk."""
    return {
        "suspicious_url": False,
        "url_risk": "Low",
        "url_reason": None,
    }
