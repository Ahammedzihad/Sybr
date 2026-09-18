"""Security rules, indicators, and heuristic definitions."""

import re
from typing import Dict, Set

# Known URL shorteners often abused in phishing campaigns
KNOWN_SHORTENERS: Set[str] = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "is.gd",
    "buff.ly",
    "ow.ly",
    "cutt.ly",
    "rb.gy",
    "shorturl.at",
    "goo.gl",
    "bl.ink",
    "rebrand.ly",
}

# High-risk / commonly abused top-level domains
SUSPICIOUS_TLDS: Set[str] = {
    "zip",
    "mov",
    "top",
    "xyz",
    "click",
    "link",
    "stream",
    "country",
    "gq",
    "cf",
    "tk",
    "ml",
    "ga",
    "buzz",
    "rest",
    "work",
    "fit",
    "surf",
    "loan",
    "tokyo",
}

# Target brands frequently spoofed
TARGET_BRANDS: Dict[str, str] = {
    "paypal": "paypal.com",
    "microsoft": "microsoft.com",
    "apple": "apple.com",
    "google": "google.com",
    "amazon": "amazon.com",
    "netflix": "netflix.com",
    "chase": "chase.com",
    "bankofamerica": "bankofamerica.com",
    "wellsfargo": "wellsfargo.com",
    "citigroup": "citi.com",
    "dropbox": "dropbox.com",
    "docusign": "docusign.com",
    "facebook": "facebook.com",
    "meta": "meta.com",
}

# Common character substitution mappings (leetspeak / lookalikes)
LOOKALIKE_MAPPINGS: Dict[str, str] = {
    "0": "o",
    "1": "l",
    "l": "i",
    "vv": "w",
    "rn": "m",
    "5": "s",
    "8": "b",
}

# Free webmail providers
FREE_MAIL_DOMAINS: Set[str] = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "aol.com",
    "mail.com",
    "proton.me",
    "protonmail.com",
    "zoho.com",
    "gmx.com",
    "yandex.com",
    "icloud.com",
}

# Sensitive organizational keywords that should not originate from free webmail
SENSITIVE_BRAND_KEYWORDS: Set[str] = {
    "paypal",
    "microsoft",
    "office365",
    "apple",
    "google",
    "amazon",
    "netflix",
    "chase",
    "bank",
    "billing",
    "invoice",
    "security",
    "it support",
    "administrator",
    "account verification",
    "payroll",
    "wire transfer",
}

# Regex for IPv4 addresses
IPV4_REGEX = re.compile(
    r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
)

# Regex for IPv6 addresses
IPV6_REGEX = re.compile(r"^\[?[a-fA-F0-9:]+\]?$")

# Phishing path indicators
SUSPICIOUS_PATH_KEYWORDS = [
    "verify",
    "login",
    "signin",
    "update-billing",
    "recover-account",
    "security-checkpoint",
    "authorize",
    "wallet-connect",
    "password-reset",
]
