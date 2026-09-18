"""Rule-based security analysis engine."""
from .rules import KNOWN_SHORTENERS, SUSPICIOUS_TLDS, LOOKALIKE_MAPPINGS
from .url_analyzer import URLAnalyzer
from .email_analyzer import EmailAnalyzer

__all__ = [
    "KNOWN_SHORTENERS",
    "SUSPICIOUS_TLDS",
    "LOOKALIKE_MAPPINGS",
    "URLAnalyzer",
    "EmailAnalyzer",
]
