"""
F9-rules & E7. Text-Cue and Social Engineering Analysis Engine.
Uses multilingual-friendly regex and keyword patterns to identify psychological manipulation and attack vectors.
"""
import re
from typing import Dict, List, Tuple, Any

# Regex patterns for social engineering cues
PATTERNS = {
    "otp_request": (
        re.compile(
            r'\b(?:otp|one[- ]time[- ]password|verification[- ]code|pin|cvv|m-?pin|security[- ]code)\b.*?\b(?:share|send|enter|verify|provide|give|tell|forward|submit)\b|\b(?:share|send|enter|verify|provide|give|tell|forward|submit)\b.*?\b(?:otp|one[- ]time[- ]password|verification[- ]code|pin|cvv|m-?pin|security[- ]code)\b',
            re.IGNORECASE,
        ),
        30,
        "OTP / PIN / CVV credential sharing requested (+30)",
        "OTP Request",
    ),
    "credential_request": (
        re.compile(
            r'\b(?:password|username|passcode|secret[- ]key|private[- ]key|login[- ]credentials|recovery[- ]phrase|seed[- ]phrase)\b.*?\b(?:enter|update|verify|confirm|share|provide|reset|submit)\b|\b(?:enter|update|verify|confirm|share|provide|reset|submit)\b.*?\b(?:password|username|passcode|secret[- ]key|private[- ]key|login[- ]credentials)\b',
            re.IGNORECASE,
        ),
        30,
        "Password or account credential submission requested (+30)",
        "Credential Harvesting",
    ),
    "payment_redirect": (
        re.compile(
            r'\b(?:gift[- ]card|apple[- ]card|steam[- ]card|amazon[- ]card|crypto|bitcoin|usdt|wire[- ]transfer|western[- ]union|transfer to (?:this|another|new) account|pay to (?:this|new) upi|send money to upi|gpay to)\b',
            re.IGNORECASE,
        ),
        25,
        "Alternative or untraceable payment redirection requested (+25)",
        "Payment Redirection",
    ),
    "remote_access": (
        re.compile(
            r'\b(?:anydesk|teamviewer|quicksupport|ultraviewer|zoho assist|logmein|rustdesk|screen[- ]share|remote[- ]access|install (?:this|the) (?:app|tool|software))\b',
            re.IGNORECASE,
        ),
        25,
        "Remote access / screen sharing tool installation requested (+25)",
        "Remote Access",
    ),
    "urgency": (
        re.compile(
            r'\b(?:urgent|immediately|immediate action|right now|within (?:24|12|48) hours|within \d+ (?:minutes|hours)|final warning|last notice|act now|expires soon|time[- ]sensitive)\b',
            re.IGNORECASE,
        ),
        10,
        "Artificial urgency or time pressure applied (+10)",
        "Urgency",
    ),
    "impersonation": (
        re.compile(
            r'\b(?:from (?:the )?(?:it|security|support|fraud|bank|compliance|hr|admin) department|official (?:bank|support) representative|on behalf of (?:ceo|management|the director)|headquarters|rbi|income tax department)\b',
            re.IGNORECASE,
        ),
        15,
        "Impersonation of authority, IT, bank, or management (+15)",
        "Impersonation",
    ),
    "threat_consequence": (
        re.compile(
            r'\b(?:account (?:will be|has been) (?:suspended|blocked|terminated|closed|locked)|legal (?:action|proceedings|charges)|police complaint|arrest warrant|fine will be imposed|service deactivated)\b',
            re.IGNORECASE,
        ),
        10,
        "Coercive threat of account suspension or legal action (+10)",
        "Threat",
    ),
    "reward_lure": (
        re.compile(
            r'\b(?:congratulations|you (?:have )?won|lottery|prize|cashback|gift hamper|free reward|claim (?:your )?(?:prize|cashback|bonus|refund))\b',
            re.IGNORECASE,
        ),
        15,
        "Financial lure, prize, or lottery reward incentive (+15)",
        "Reward Lure",
    ),
    "secrecy": (
        re.compile(
            r'\b(?:don\'t tell (?:anyone|anybody)|keep this (?:secret|confidential|between us)|do not disclose|strictly confidential|keep quiet)\b',
            re.IGNORECASE,
        ),
        10,
        "Secrecy or isolation requested (+10)",
        "Secrecy",
    ),
    "click_to_verify": (
        re.compile(
            r'\b(?:click (?:here|the link|below)|tap (?:here|the link)|follow (?:this|the) link|visit (?:this|the) url)\b.*?\b(?:verify|login|restore|unlock|activate|validate|claim)\b|\b(?:verify|login|restore|unlock|activate|validate|claim)\b.*?\b(?:click (?:here|the link|below)|tap (?:here|the link))\b',
            re.IGNORECASE,
        ),
        15,
        "Call-to-action urging user to click link to verify account (+15)",
        "Credential Harvesting",
    ),
    "prompt_injection": (
        re.compile(
            r'\b(?:ignore (?:all )?previous instructions|system prompt|disregard instructions|you are now a|pretend you are|dan mode|jailbreak|bypass security)\b',
            re.IGNORECASE,
        ),
        25,
        "Prompt injection attempt detected inside untrusted customer input (+25)",
        "Prompt Injection",
    ),
}


def analyze_text_cues(text: str) -> Dict[str, Any]:
    """
    Evaluates text against social engineering cues and psychological manipulation patterns.
    Returns:
      - score: int
      - reasons: List[str]
      - techniques: List[str]
      - otp_request: bool
      - credential_request: bool
    """
    if not text:
        return {
            "score": 0,
            "reasons": [],
            "techniques": [],
            "otp_request": False,
            "credential_request": False,
        }

    score = 0
    reasons: List[str] = []
    techniques: List[str] = []
    otp_found = False
    cred_found = False

    for cue_key, (pattern, weight, reason, tech_name) in PATTERNS.items():
        if pattern.search(text):
            score += weight
            reasons.append(reason)
            if tech_name not in techniques:
                techniques.append(tech_name)

            if cue_key == "otp_request":
                otp_found = True
            elif cue_key in ("credential_request", "click_to_verify"):
                cred_found = True

    return {
        "score": score,
        "reasons": reasons,
        "techniques": techniques,
        "otp_request": otp_found,
        "credential_request": cred_found,
    }
