"""
Configuration settings, controlled vocabularies, and environment variables.
"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Section 5: Fixed Categories
CATEGORIES: List[str] = [
    "Billing/Payment",
    "Account/Login",
    "Product Issue",
    "Delivery/Shipping",
    "Refund Request",
    "Subscription Issue",
    "Technical Problem",
    "Service Quality",
    "Security Concern",
    "Other",
]

# Section 5: Controlled Vocabulary for Issue Labels
ISSUE_LABELS: List[str] = [
    "Login Failure",
    "Password Reset",
    "Payment Failure",
    "Duplicate Charge",
    "Refund Delay",
    "Delivery Delay",
    "Wrong/Damaged Item",
    "Order Not Confirmed",
    "Subscription Cancellation",
    "App Crash/Bug",
    "Service Outage",
    "Account Compromise",
    "Unauthorized Transaction",
    "Phishing Attempt",
    "Poor Support Experience",
    "Other",
]

CHANNELS: List[str] = ["email", "chat", "ticket", "social", "form", "sms", "voice"]
SENTIMENTS: List[str] = ["Positive", "Neutral", "Negative"]
EMOTIONS: List[str] = [
    "Anger",
    "Frustration",
    "Satisfaction",
    "Confusion",
    "Urgency",
    "Disappointment",
    "Fear",
    "Neutral",
]
PRIORITY_LEVELS: List[str] = ["Low", "Medium", "High", "Critical"]
RISK_LEVELS: List[str] = ["Low", "Medium", "High", "Critical"]
RESOLUTION_STATUSES: List[str] = ["Resolved", "Unresolved", "Pending"]
THREAT_TYPES: List[str] = [
    "Phishing",
    "Social Engineering",
    "Impersonation",
    "Malware Attachment",
    "None",
]
SOCIAL_ENGINEERING_VALUES: List[str] = ["Yes", "Possible", "No"]
TECHNIQUES: List[str] = [
    "Urgency",
    "Credential Harvesting",
    "OTP Request",
    "Impersonation",
    "Reward Lure",
    "Payment Redirection",
    "Remote Access",
    "Secrecy",
    "Threat",
    "Prompt Injection",
]


class Settings:
    """Application settings loaded from environment variables."""
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").strip()
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    ORG_DOMAINS: List[str] = [
        d.strip().lower()
        for d in os.getenv("ORG_DOMAINS", "mycompany.com,support.mycompany.com").split(",")
        if d.strip()
    ]
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    CORS_ORIGINS: List[str] = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175",
        ).split(",")
        if o.strip()
    ]
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").strip()


settings = Settings()
