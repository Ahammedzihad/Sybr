"""
Section 15. Golden Demo Integration Cases.
Validates the 7 exact golden benchmark scenarios specified in the master prompt.
"""
import pytest
from app.pipeline import process_conversation
from app.schemas import Message, SecurityDetail
from app.security.scoring import evaluate_security_rules


def test_golden_case_1_charged_twice():
    """
    Case 1: "charged twice, please refund"
    Expects: Billing/Payment, Duplicate Charge, Negative sentiment, High priority.
    """
    conv = {
        "conversation_id": "GOLDEN-1",
        "channel": "chat",
        "text": "I was charged twice, please refund the second charge immediately.",
        "source": "real",
    }
    record = process_conversation(conv, persist=False)
    assert record.category == "Billing/Payment"
    assert record.issue_label == "Duplicate Charge"
    assert record.sentiment in ("Negative", "Neutral")
    assert record.priority in ("High", "Critical")


def test_golden_case_2_unauthorized_transfer():
    """
    Case 2: "someone transferred ₹25,000 without permission"
    Expects: Critical priority, Security Concern / Unauthorized Transaction, Immediate security investigation.
    """
    conv = {
        "conversation_id": "GOLDEN-2",
        "channel": "ticket",
        "text": "Emergency! Someone transferred ₹25,000 without permission from my bank account! Please block this!",
        "source": "real",
    }
    record = process_conversation(conv, persist=False)
    assert record.priority == "Critical"
    assert record.category == "Security Concern"
    assert record.issue_label == "Unauthorized Transaction"
    assert "investigation" in record.security.recommended_action.lower() or "escalate" in record.security.recommended_action.lower()


def test_golden_case_3_urgent_phishing_otp():
    """
    Case 3: "URGENT! Your account has been compromised. Click this link immediately and enter your username, password and OTP."
    Expects: Phishing, Yes (social eng), Urgency + Credential Harvesting + OTP, Critical risk.
    """
    conv = {
        "conversation_id": "GOLDEN-3",
        "channel": "email",
        "text": "URGENT! Your account has been compromised. Click http://verify-secure.top/login immediately and enter your username, password and OTP.",
        "source": "synthetic",
    }
    record = process_conversation(conv, persist=False)
    assert record.security.threat_detected is True
    assert record.security.threat_type == "Phishing"
    assert record.security.social_engineering in ("Yes", "Possible")
    assert record.security.otp_request is True
    assert record.security.credential_request is True
    assert record.security.risk_level == "Critical"
    assert any("Urgency" in t for t in record.security.techniques)


def test_golden_case_4_lookalike_url():
    """
    Case 4: "Please verify at http://paypa1-security.example/login"
    Expects: Lookalike detected (paypal), High or Critical risk.
    """
    conv = {
        "conversation_id": "GOLDEN-4",
        "channel": "chat",
        "text": "Please verify at http://paypa1-security.example/login",
        "source": "synthetic",
    }
    record = process_conversation(conv, persist=False)
    assert record.security.suspicious_url is True
    assert any(u.lookalike_of == "paypal" for u in record.security.urls)
    assert record.security.risk_level in ("High", "Critical")


def test_golden_case_5_email_spoofing():
    """
    Case 5: "support@paypa1-security.example"
    Expects: Potential impersonation, domain mismatch, lookalike of paypal.
    """
    sec = evaluate_security_rules(
        "Hello customer, please review your account activity.",
        explicit_emails=[("PayPal Official Support", "support@paypa1-security.example")]
    )
    assert sec.suspicious_email is True
    assert any(e.lookalike_of == "paypal" for e in sec.emails)
    assert sec.emails[0].domain_mismatch is True


def test_golden_case_6_three_message_unpaid_refund():
    """
    Case 6: Three-message unpaid-refund thread
    Expects: Unresolved status, High priority.
    """
    thread = [
        Message(sender="customer", text="I am still waiting for my refund of $70."),
        Message(sender="agent", text="We are looking into the transaction ID."),
        Message(sender="customer", text="Again writing for the third time, why no response? Still no refund!"),
    ]
    conv = {
        "conversation_id": "GOLDEN-6",
        "channel": "ticket",
        "messages": thread,
        "source": "real",
    }
    record = process_conversation(conv, persist=False)
    assert record.resolution_status == "Unresolved"
    assert record.priority in ("High", "Critical")


def test_golden_case_7_twenty_five_message_thread():
    """
    Case 7: 25-message thread
    Expects: Produces structured 5-point summary without crashing or truncating schema.
    """
    long_thread = []
    for i in range(1, 26):
        role = "customer" if i % 2 != 0 else "agent"
        long_thread.append(
            Message(
                sender=role,
                text=f"Message step {i}: Discussing technical problem with the payment gateway integration and invoice #{i}.",
            )
        )
    conv = {
        "conversation_id": "GOLDEN-7",
        "channel": "ticket",
        "messages": long_thread,
        "source": "real",
    }
    record = process_conversation(conv, persist=False)
    assert record.summary.issue != ""
    assert record.summary.customer_request != ""
    assert record.summary.actions_taken != ""
    assert record.summary.current_status != ""
    assert record.summary.priority != ""
    assert len(record.messages) == 25


def test_readme_golden_case_1_routine_complaint():
    """Case 1: Routine customer complaint (legitimate)."""
    conv = {
        "text": "Hello, my order #48291 arrived with the wrong size shirt. Can I get an exchange?",
        "channel": "chat"
    }
    rec = process_conversation(conv, persist=False)
    assert rec.security.threat_detected is False
    assert rec.security.risk_level == "Low"


def test_readme_golden_case_2_spoofed_brand_lookalike():
    """Case 2: Spoofed brand and lookalike domain (typosquatting)."""
    conv = {
        "text": "Please confirm your account login at http://paypa1-security.example/login to restore privileges.",
        "channel": "email"
    }
    rec = process_conversation(conv, persist=False)
    assert rec.security.suspicious_url is True
    assert rec.security.threat_detected is True
    assert any(u.lookalike_of == "paypal" for u in rec.security.urls)


def test_readme_golden_case_3_display_name_freemail_mismatch():
    """Case 3: Display-name brand mismatch / free-mail spoofing."""
    conv = {
        "text": "Dear customer, this is PayPal Support. Please reply with your invoice number.",
        "channel": "email",
        "emails": [("PayPal Support", "security-desk@gmail.com")]
    }
    rec = process_conversation(conv, persist=False)
    assert rec.security.suspicious_email is True
    assert rec.security.emails[0].free_mail is True


def test_readme_golden_case_4_urgent_suspension_hidden_link():
    """Case 4: Urgent account suspension with hidden link."""
    conv = {
        "text": "URGENT: Your account has been suspended! Restore immediate access here: http://192.168.1.50/reactivate",
        "channel": "email"
    }
    rec = process_conversation(conv, persist=False)
    assert rec.security.threat_detected is True
    assert rec.security.suspicious_url is True
    assert any(u.ip_literal is True for u in rec.security.urls)


def test_readme_golden_case_5_dangerous_attachment():
    """Case 5: Dangerous attachment with double extension."""
    conv = {
        "text": "Please check the attached payment proof.",
        "channel": "email",
        "attachments": ["supplier_remittance.pdf.exe"]
    }
    rec = process_conversation(conv, persist=False)
    assert rec.security.suspicious_attachment is True
    assert rec.security.risk_level in ("High", "Critical")


def test_readme_golden_case_6_otp_fraud_override():
    """Case 6: WhatsApp/SMS OTP fraud with rule override."""
    conv = {
        "text": "Bank Alert: $500 deducted. If this wasn't you, open http://bank-cancel.top and submit OTP.",
        "channel": "sms"
    }
    rec = process_conversation(conv, persist=False)
    assert rec.security.threat_detected is True
    assert rec.security.otp_request is True
    assert rec.security.risk_level == "Critical"


def test_readme_golden_case_7_urgency_false_positive_defense():
    """Case 7: Legitimate inquiry containing urgency cues (false-positive defense)."""
    conv = {
        "text": "URGENT: My flight departs in 2 hours and I haven't received my booking confirmation email! Please help immediately!",
        "channel": "chat"
    }
    rec = process_conversation(conv, persist=False)
    # Urgency in customer request must NOT trigger Phishing threat or Critical security risk
    assert rec.security.threat_detected is False
    assert rec.security.threat_type == "None"
    assert rec.security.risk_level == "Low"
    assert rec.priority in ("High", "Critical")  # High support priority is legitimate

