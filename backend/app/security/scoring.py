"""
F9 & Section 8. Security Scoring, Risk Banding, and Override Rules.
Integrates URL, email, attachment, and text cue signals into an explainable security assessment.
"""
import re
from typing import List, Tuple, Dict, Any, Optional
from app.schemas import (
    SecurityDetail,
    UrlFinding,
    EmailFinding,
    AttachmentFinding,
)
from app.security.url_check import extract_urls, analyze_url
from app.security.email_check import extract_emails_from_text, analyze_email
from app.security.attachment_check import analyze_attachment
from app.security.text_cues import analyze_text_cues


RISK_SEVERITY_ORDER = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Critical": 4,
}

PRIORITY_SEVERITY_ORDER = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Critical": 4,
}

SEVERITY_TO_PRIORITY = {v: k for k, v in PRIORITY_SEVERITY_ORDER.items()}
SEVERITY_TO_RISK = {v: k for k, v in RISK_SEVERITY_ORDER.items()}


def score_to_band(score: int) -> str:
    """Maps deterministic rule score (0-100) to standard risk band."""
    if score >= 75:
        return "Critical"
    elif score >= 50:
        return "High"
    elif score >= 25:
        return "Medium"
    else:
        return "Low"


def evaluate_security_rules(
    text: str,
    explicit_urls: Optional[List[str]] = None,
    explicit_emails: Optional[List[Tuple[str, str]]] = None,
    explicit_attachments: Optional[List[str]] = None,
) -> SecurityDetail:
    """
    Master rule evaluator. Runs deterministic checks on URLs, emails, attachments, and text cues.
    Returns fully populated and explainable SecurityDetail.
    """
    # 1. URL Analysis
    found_urls = list(explicit_urls or [])
    if not explicit_urls:
        found_urls.extend(extract_urls(text))

    url_findings: List[UrlFinding] = [analyze_url(u) for u in set(found_urls)]
    suspicious_url = any(
        u.risk in ("Medium", "High") or bool(u.lookalike_of) or u.ip_literal or u.shortener
        for u in url_findings
    )
    suspicious_domain = any(bool(u.lookalike_of or u.ip_literal) for u in url_findings)

    # 2. Email Analysis
    found_emails = list(explicit_emails or [])
    if not explicit_emails:
        found_emails.extend(extract_emails_from_text(text))

    email_findings: List[EmailFinding] = [
        analyze_email(addr, name) for name, addr in found_emails
    ]
    suspicious_email = any(e.risk in ("Medium", "High") for e in email_findings)
    if any(bool(e.lookalike_of) for e in email_findings):
        suspicious_domain = True

    # 3. Attachment Analysis
    attachment_findings: List[AttachmentFinding] = [
        analyze_attachment(att) for att in (explicit_attachments or [])
    ]
    suspicious_attachment = any(a.risk in ("Medium", "High") for a in attachment_findings)

    # 4. Text-cue Analysis
    text_results = analyze_text_cues(text)
    techniques: List[str] = text_results["techniques"]
    otp_request: bool = text_results["otp_request"]
    credential_request: bool = text_results["credential_request"]

    # 5. Aggregate Rule Score (sum all signals, capped at 100)
    raw_score = 0
    all_reasons: List[str] = []

    # Extract point values from reasons formatted like "(+30)"
    point_regex = re.compile(r'\(\+(\d+)\)')

    for u in url_findings:
        if u.reasons:
            all_reasons.extend(u.reasons)
            for r in u.reasons:
                m = point_regex.search(r)
                if m:
                    raw_score += int(m.group(1))

    for e in email_findings:
        if e.reasons:
            all_reasons.extend(e.reasons)
            for r in e.reasons:
                m = point_regex.search(r)
                if m:
                    raw_score += int(m.group(1))

    for a in attachment_findings:
        if a.reasons:
            all_reasons.extend(a.reasons)
            for r in a.reasons:
                m = point_regex.search(r)
                if m:
                    raw_score += int(m.group(1))

    if text_results["reasons"]:
        all_reasons.extend(text_results["reasons"])
        raw_score += text_results["score"]

    total_rule_score = min(100, raw_score)
    risk_band = score_to_band(total_rule_score)

    # If any individual URL, email, or attachment is High, risk band should be at least High
    if any(u.risk == "High" for u in url_findings) or any(e.risk == "High" for e in email_findings) or any(a.risk == "High" for a in attachment_findings):
        if RISK_SEVERITY_ORDER[risk_band] < RISK_SEVERITY_ORDER["High"]:
            risk_band = "High"

    # 6. Override Rule 8.6:
    # "OTP or credential request AND suspicious URL/domain -> minimum Critical."
    has_cred_or_otp = otp_request or credential_request
    has_suspicious_link = suspicious_url or suspicious_domain
    if has_cred_or_otp and has_suspicious_link:
        risk_band = "Critical"
        override_reason = "Critical Override: Credential/OTP harvesting combined with suspicious/lookalike URL or domain"
        if override_reason not in all_reasons:
            all_reasons.insert(0, override_reason)

    # 7. Threat type & Social engineering classification
    # Genuine complaints (e.g. asking for immediate refund or saying urgent) with low score (0-24)
    # and no attack indicators (links, attachments, spoofing, credentials, remote access) are NOT threats.
    has_active_attack_indicator = (
        suspicious_url
        or suspicious_domain
        or suspicious_email
        or suspicious_attachment
        or otp_request
        or credential_request
        or "Remote Access" in techniques
        or "Payment Redirection" in techniques
        or "Prompt Injection" in techniques
    )

    threat_detected = (
        risk_band in ("High", "Critical")
        or (risk_band == "Medium" and has_active_attack_indicator)
        or (risk_band == "Low" and (suspicious_url or suspicious_attachment or has_cred_or_otp))
    )

    threat_type = "None"
    if suspicious_attachment and any(
        a.extension in ("exe", "vbs", "bat", "docm", "scr") for a in attachment_findings
    ):
        threat_type = "Malware Attachment"
    elif (suspicious_url or suspicious_domain) and (credential_request or otp_request):
        threat_type = "Phishing"
    elif suspicious_email and any(e.domain_mismatch for e in email_findings):
        threat_type = "Impersonation"
    elif threat_detected and techniques and (
        "Remote Access" in techniques
        or "Payment Redirection" in techniques
        or "Reward Lure" in techniques
    ):
        threat_type = "Social Engineering"
    elif threat_detected:
        threat_type = "Phishing"

    # Social engineering flag
    if threat_detected:
        if len(techniques) >= 2 or ("Urgency" in techniques and has_cred_or_otp) or "Remote Access" in techniques:
            social_engineering = "Yes"
        elif len(techniques) >= 1 or has_cred_or_otp:
            social_engineering = "Possible"
        else:
            social_engineering = "No"
    else:
        social_engineering = "No"

    # Recommended Action
    if risk_band == "Critical":
        recommended_action = (
            "Escalate to security team immediately; do not click any links, share credentials, or run attachments"
        )
    elif risk_band == "High":
        recommended_action = (
            "Escalate to security team; verify sender authenticity through official out-of-band channels"
        )
    elif risk_band == "Medium":
        recommended_action = (
            "Caution advised; verify links and sender identity before taking any requested actions"
        )
    else:
        recommended_action = "Normal customer support handling; no active security threats identified"

    return SecurityDetail(
        threat_detected=threat_detected,
        threat_type=threat_type,
        social_engineering=social_engineering,
        techniques=techniques,
        suspicious_url=suspicious_url,
        suspicious_domain=suspicious_domain,
        suspicious_email=suspicious_email,
        suspicious_attachment=suspicious_attachment,
        credential_request=credential_request,
        otp_request=otp_request,
        urls=url_findings,
        emails=email_findings,
        attachments=attachment_findings,
        rule_score=total_rule_score,
        risk_level=risk_band,
        risk_reasons=all_reasons[:10],  # Keep explainable and concise
        recommended_action=recommended_action,
    )


def apply_merge_and_overrides(
    security_detail: SecurityDetail,
    gemini_risk: Optional[str] = None,
    sentiment: str = "Neutral",
    is_angry: bool = False,
    urgency: str = "Low",
    priority: str = "Low",
    priority_reason: str = "",
    resolution_status: str = "Pending",
    category: str = "Other",
) -> Tuple[SecurityDetail, str, str, str]:
    """
    Section 8.6:
    - Final risk_level = max(rule band, Gemini risk_level) (AI can raise, never lower).
    - If is_angry or urgency = High and unresolved -> raise priority one level (cap Critical).
    - Security threat detected with High/Critical risk -> set priority to at least High and category may become Security Concern.
    Returns: (updated_security, final_priority, final_priority_reason, final_category)
    """
    # 1. Risk level: AI can raise, never lower below rule band
    rule_level = security_detail.risk_level
    if gemini_risk and gemini_risk in RISK_SEVERITY_ORDER:
        if RISK_SEVERITY_ORDER[gemini_risk] > RISK_SEVERITY_ORDER[rule_level]:
            security_detail.risk_level = gemini_risk
            security_detail.risk_reasons.append(
                f"AI elevated risk level from {rule_level} to {gemini_risk} based on contextual threat signals"
            )

    final_priority = priority
    final_priority_reason = priority_reason
    final_category = category

    # 2. Priority escalation for angry/high urgency unresolved issues (Section 8.6 & E2)
    current_priority_val = PRIORITY_SEVERITY_ORDER.get(final_priority, 1)
    if resolution_status == "Unresolved":
        if current_priority_val < 4:
            current_priority_val += 1
            final_priority = SEVERITY_TO_PRIORITY[current_priority_val]
            escalation_msg = "Escalated priority due to unresolved customer complaint follow-up."
            final_priority_reason = (
                f"{final_priority_reason}; {escalation_msg}" if final_priority_reason else escalation_msg
            )

    # 3. Security threat detected with High/Critical risk -> priority at least High
    if security_detail.risk_level in ("High", "Critical") and security_detail.threat_detected:
        if PRIORITY_SEVERITY_ORDER.get(final_priority, 1) < PRIORITY_SEVERITY_ORDER["High"]:
            final_priority = "High"
            sec_reason = "Priority elevated to High due to active security threat."
            final_priority_reason = (
                f"{final_priority_reason}; {sec_reason}" if final_priority_reason else sec_reason
            )
        if security_detail.risk_level == "Critical":
            final_priority = "Critical"

        if final_category in ("Other", "General"):
            final_category = "Security Concern"

    # If critical security concern reported by customer (e.g. unauthorized transfer, account compromise)
    if final_priority == "Critical" and final_category == "Security Concern":
        security_detail.recommended_action = "Immediate security investigation; secure account and freeze unauthorized transactions."

    return security_detail, final_priority, final_priority_reason, final_category
