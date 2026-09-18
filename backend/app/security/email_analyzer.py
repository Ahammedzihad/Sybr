"""Rule-based Email Sender security analyzer."""

import re
from typing import Any, Dict, List
import tldextract

from app.security.rules import (
    FREE_MAIL_DOMAINS,
    LOOKALIKE_MAPPINGS,
    SENSITIVE_BRAND_KEYWORDS,
    SUSPICIOUS_TLDS,
    TARGET_BRANDS,
)

# Email address extraction regex
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$")


class EmailAnalyzer:
    """
    Extensible Email analyzer that detects address spoofing, free-mail mismatches,
    lookalike sender domains, and anomalous header patterns.
    """

    def __init__(self):
        self._extract = tldextract.TLDExtract(suffix_list_urls=None)

    def _get_registered_domain(self, ext, domain: str) -> str:
        """Helper to get registered domain across tldextract versions."""
        top_domain = getattr(ext, "top_domain_under_public_suffix", None)
        if top_domain:
            return top_domain.lower()
        if hasattr(ext, "domain") and hasattr(ext, "suffix") and ext.domain and ext.suffix:
            return f"{ext.domain}.{ext.suffix}".lower()
        return domain.lower()

    def analyze(self, sender: str, subject: str = "", message_preview: str = "") -> Dict[str, Any]:
        """
        Analyzes a sender address and contextual subject for phishing indicators.
        """
        indicators: List[str] = []
        details: List[Dict[str, str]] = []
        is_suspicious = False

        cleaned_sender = sender.strip()

        # Extract email address if enclosed in brackets like "John Doe <john@example.com>"
        display_name = ""
        email_addr = cleaned_sender
        if "<" in cleaned_sender and ">" in cleaned_sender:
            match = re.search(r"^(.*?)\s*<([^>]+)>", cleaned_sender)
            if match:
                display_name = match.group(1).strip()
                email_addr = match.group(2).strip()

        # 1. Format check
        if not EMAIL_REGEX.match(email_addr):
            is_suspicious = True
            indicators.append("invalid_email_format")
            details.append({
                "indicator": "invalid_email_format",
                "severity": "High",
                "description": f"Sender address '{email_addr}' is not a valid RFC-compliant email address",
            })
            domain = ""
        else:
            domain = email_addr.split("@")[1].lower()

        if domain:
            ext = self._extract(domain)
            registered_domain = self._get_registered_domain(ext, domain)
            tld = ext.suffix.lower()

            # 2. Check Suspicious TLD
            if tld in SUSPICIOUS_TLDS:
                is_suspicious = True
                indicators.append("suspicious_sender_tld")
                details.append({
                    "indicator": "suspicious_sender_tld",
                    "severity": "High",
                    "description": f"Sender domain uses high-abuse top-level domain (.{tld})",
                })

            # 3. Check Free-mail Domain Mismatch with Institutional / Financial Keywords
            context_text = f"{display_name} {subject} {message_preview}".lower()
            is_freemail = registered_domain in FREE_MAIL_DOMAINS

            if is_freemail:
                for keyword in SENSITIVE_BRAND_KEYWORDS:
                    if keyword in context_text:
                        is_suspicious = True
                        indicators.append("freemail_brand_spoofing")
                        details.append({
                            "indicator": "freemail_brand_spoofing",
                            "severity": "Critical",
                            "description": f"Sender uses free public email provider ({registered_domain}) while referencing sensitive entity or action ('{keyword}')",
                        })
                        break

            # 4. Check Lookalike / Typosquatted Domain in Sender
            normalized_domain = ext.domain.lower()
            for char, sub in LOOKALIKE_MAPPINGS.items():
                normalized_domain = normalized_domain.replace(char, sub)

            for brand, official_domain in TARGET_BRANDS.items():
                if brand in normalized_domain and registered_domain != official_domain:
                    is_suspicious = True
                    indicators.append("lookalike_sender_domain")
                    details.append({
                        "indicator": "lookalike_sender_domain",
                        "severity": "Critical",
                        "description": f"Sender domain '{registered_domain}' is a lookalike of official '{official_domain}'",
                    })
                    break

            # 5. Check Suspicious Local-Part Randomness (e.g., long hex strings or random digits)
            local_part = email_addr.split("@")[0]
            if len(local_part) > 15 and sum(c.isdigit() for c in local_part) > 6:
                indicators.append("anomalous_localpart")
                details.append({
                    "indicator": "anomalous_localpart",
                    "severity": "Medium",
                    "description": "Sender username contains anomalous random character patterns",
                })

        # Determine overall suspicious flag
        if any(d["severity"] in ("Critical", "High") for d in details):
            is_suspicious = True

        return {
            "sender": sender,
            "email": email_addr,
            "display_name": display_name,
            "is_suspicious": is_suspicious,
            "indicators": indicators,
            "details": details,
        }
