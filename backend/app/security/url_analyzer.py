"""Rule-based URL security analyzer."""

import re
from typing import Any, Dict, List
from urllib.parse import urlparse
import tldextract

from app.security.rules import (
    IPV4_REGEX,
    IPV6_REGEX,
    KNOWN_SHORTENERS,
    LOOKALIKE_MAPPINGS,
    SUSPICIOUS_PATH_KEYWORDS,
    SUSPICIOUS_TLDS,
    TARGET_BRANDS,
)


class URLAnalyzer:
    """
    Extensible URL analyzer that detects phishing indicators,
    domain anomalies, and suspicious formatting.
    """

    def __init__(self):
        # Extract domain info without network requests
        self._extract = tldextract.TLDExtract(suffix_list_urls=None)

    def analyze(self, url: str) -> Dict[str, Any]:
        """
        Analyzes a single URL for security threats.
        Returns a dictionary of indicators, flags, and details.
        """
        indicators: List[str] = []
        is_suspicious = False
        details: List[Dict[str, str]] = []

        raw_url = url.strip()
        if not raw_url:
            return {
                "url": url,
                "is_suspicious": False,
                "indicators": [],
                "details": [],
            }

        # Ensure scheme is present for parsing
        parse_target = raw_url
        if not (raw_url.startswith("http://") or raw_url.startswith("https://")):
            parse_target = "http://" + raw_url

        try:
            parsed = urlparse(parse_target)
        except Exception:
            return {
                "url": url,
                "is_suspicious": True,
                "indicators": ["malformed_url"],
                "details": [{"indicator": "malformed_url", "severity": "High", "description": "URL cannot be parsed safely"}],
            }

        hostname = (parsed.hostname or "").lower()
        path = parsed.path.lower()

        # 1. Check Missing HTTPS
        if raw_url.startswith("http://"):
            indicators.append("missing_https")
            details.append({
                "indicator": "missing_https",
                "severity": "Medium",
                "description": "Communication lacks TLS encryption (uses plain HTTP)",
            })

        # 2. Check IP-Literal Hostname
        if IPV4_REGEX.match(hostname) or (hostname.startswith("[") and IPV6_REGEX.match(hostname)):
            is_suspicious = True
            indicators.append("ip_literal_url")
            details.append({
                "indicator": "ip_literal_url",
                "severity": "Critical",
                "description": f"URL uses raw IP address instead of a domain name ({hostname})",
            })

        # 3. Check URL Shorteners
        ext = self._extract(hostname)
        registered_domain = ext.registered_domain.lower() if ext.registered_domain else hostname

        if registered_domain in KNOWN_SHORTENERS:
            is_suspicious = True
            indicators.append("url_shortener")
            details.append({
                "indicator": "url_shortener",
                "severity": "Medium",
                "description": f"URL uses known shortening service ({registered_domain}) to mask destination",
            })

        # 4. Check High-Risk Suspicious TLD
        tld = ext.suffix.lower()
        if tld in SUSPICIOUS_TLDS:
            is_suspicious = True
            indicators.append("suspicious_tld")
            details.append({
                "indicator": "suspicious_tld",
                "severity": "High",
                "description": f"Domain uses high-abuse top-level domain (.{tld})",
            })

        # 5. Check Obfuscated Host / @ Symbol in Authority
        if "@" in parsed.netloc:
            is_suspicious = True
            indicators.append("userinfo_obfuscation")
            details.append({
                "indicator": "userinfo_obfuscation",
                "severity": "Critical",
                "description": "URL uses '@' symbol in authority to deceive browser and redirect",
            })

        # Check Punycode / IDN
        if hostname.startswith("xn--") or ".xn--" in hostname:
            is_suspicious = True
            indicators.append("punycode_domain")
            details.append({
                "indicator": "punycode_domain",
                "severity": "High",
                "description": "Domain uses punycode/IDN internationalized characters often used for visual spoofing",
            })

        # 6. Check Excessive Subdomains
        subdomain = ext.subdomain
        if subdomain:
            subdomain_parts = [p for p in subdomain.split(".") if p]
            if len(subdomain_parts) >= 3:
                is_suspicious = True
                indicators.append("excessive_subdomains")
                details.append({
                    "indicator": "excessive_subdomains",
                    "severity": "Medium",
                    "description": f"Domain contains excessive nested subdomains ({subdomain})",
                })

        # 7. Check Lookalike / Typosquatting of Brands
        normalized_domain = ext.domain.lower()
        for char, sub in LOOKALIKE_MAPPINGS.items():
            normalized_domain = normalized_domain.replace(char, sub)

        for brand, official_domain in TARGET_BRANDS.items():
            if brand in normalized_domain and registered_domain != official_domain:
                is_suspicious = True
                indicators.append("lookalike_domain")
                details.append({
                    "indicator": "lookalike_domain",
                    "severity": "Critical",
                    "description": f"Domain name mimics legitimate brand '{brand}' ({registered_domain} vs {official_domain})",
                })
                break

        # 8. Check Suspicious Keywords in Path on Unknown Domains
        if any(keyword in path for keyword in SUSPICIOUS_PATH_KEYWORDS):
            if registered_domain not in TARGET_BRANDS.values():
                indicators.append("suspicious_path_keywords")
                details.append({
                    "indicator": "suspicious_path_keywords",
                    "severity": "Low",
                    "description": f"URL path contains credential or account manipulation keywords ({path})",
                })

        # If any high or critical indicator was flagged, mark suspicious
        if any(d["severity"] in ("Critical", "High") for d in details):
            is_suspicious = True

        return {
            "url": url,
            "is_suspicious": is_suspicious,
            "indicators": indicators,
            "details": details,
        }

    def analyze_many(self, urls: List[str]) -> Dict[str, Any]:
        """Analyzes a list of URLs and combines all indicators."""
        all_indicators: List[str] = []
        all_details: List[Dict[str, str]] = []
        any_suspicious = False
        url_results = []

        for u in urls:
            res = self.analyze(u)
            url_results.append(res)
            if res["is_suspicious"]:
                any_suspicious = True
            for ind in res["indicators"]:
                if ind not in all_indicators:
                    all_indicators.append(ind)
            all_details.extend(res["details"])

        return {
            "suspicious_url": any_suspicious,
            "indicators": all_indicators,
            "details": all_details,
            "url_results": url_results,
        }
