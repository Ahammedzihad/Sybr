"""
Email security check module.
Stub implementation returning safe placeholder results.
"""

from typing import Any, Dict


def check_email(email: str) -> Dict[str, Any]:
    """Stub function to check email address risk."""
    return {
        "suspicious_email": False,
        "email_risk": "Low",
        "email_reason": None,
    }
