"""
F2 & Section 13. Text Preprocessing, PII Masking, and Local Keyword Extraction (F5).
Cleans customer text, strips PII for privacy, and computes TF-IDF keywords without external AI.
"""
import re
import string
from typing import List, Tuple
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()

# ---------------------------------------------------------------------------
# PII Masking Regular Expressions
# ---------------------------------------------------------------------------

# Credit / Debit card: 13-19 digits formatted with spaces or hyphens, or 16 contiguous digits
CARD_REGEX = re.compile(
    r'\b(?:\d{4}[-\s]){3}\d{4}\b|\b(?:\d{4}[-\s]){2}\d{4}[-\s]\d{3}\b|\b\d{15,16}\b'
)

# Indian Aadhaar: 12 digits, often 4-4-4
AADHAAR_REGEX = re.compile(
    r'\b[2-9]\d{3}[-\s]\d{4}[-\s]\d{4}\b|\b[2-9]\d{11}\b'
)

# Indian PAN card: 5 uppercase letters, 4 digits, 1 uppercase letter
PAN_REGEX = re.compile(
    r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
)

# Phone numbers (international, Indian 10-digit starting with 6-9, standard US formats)
PHONE_REGEX = re.compile(
    r'(?:\+?91[-\s]?)?[6-9]\d{9}\b|(?:\+?1[-\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
)

# OTP code patterns (e.g. "otp: 489201", "OTP is 5912", "code 948201")
OTP_CONTEXT_REGEX = re.compile(
    r'(?i)\b(?:otp|one[- ]time[- ]password|verification[- ]code|pin|security code)(?:\s*(?:is|:|=|-)\s*)([0-9]{4,8})\b'
)


def mask_pii(text: str) -> str:
    """
    Masks personal identifiable information (PII) before storage and external API calls.
    Preserves URLs and email domains for security analysis.
    """
    if not text:
        return ""

    masked = text

    # Mask OTP with preceding context
    masked = OTP_CONTEXT_REGEX.sub(r'OTP: [OTP]', masked)

    # Mask Credit/Debit cards
    masked = CARD_REGEX.sub('[CARD]', masked)

    # Mask Aadhaar numbers
    masked = AADHAAR_REGEX.sub('[AADHAAR]', masked)

    # Mask PAN card numbers
    masked = PAN_REGEX.sub('[PAN]', masked)

    # Mask Phone numbers
    masked = PHONE_REGEX.sub('[PHONE]', masked)

    return masked


# ---------------------------------------------------------------------------
# Text Cleaning & Normalization
# ---------------------------------------------------------------------------

CONTRACTIONS = {
    "won't": "will not",
    "can't": "cannot",
    "n't": " not",
    "'re": " are",
    "'s": " is",
    "'d": " would",
    "'ll": " will",
    "'ve": " have",
    "'m": " am",
}

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than",
    "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's",
    "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom",
    "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
    "you're", "you've", "your", "yours", "yourself", "yourselves",
    # Customer support filler and temporal noise words
    "please", "pls", "dear", "sir", "madam", "hello", "hi", "hey", "thanks",
    "thank", "help", "need", "want", "like", "get", "know", "also", "just",
    "yesterday", "today", "tomorrow", "time", "day", "days", "date", "hours",
    "minutes", "ago", "still", "now", "well", "way", "going", "said", "told"
}


def expand_contractions(text: str) -> str:
    """Expands English conversational contractions."""
    clean = text
    for contraction, expansion in CONTRACTIONS.items():
        clean = re.sub(re.escape(contraction), expansion, clean, flags=re.IGNORECASE)
    return clean


def clean_text(text: str) -> str:
    """
    F2: Lowercases, removes HTML tags, normalizes whitespace, and expands contractions.
    Keeps original intact for display; cleaned text is used for tokens/TF-IDF.
    """
    if not text:
        return ""

    # Remove HTML tags
    cleaned = re.sub(r'<[^>]+>', ' ', text)

    # Expand contractions
    cleaned = expand_contractions(cleaned)

    # Lowercase
    cleaned = cleaned.lower()

    # Remove non-alphanumeric except spaces
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', cleaned)

    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned


def simple_lemmatize(token: str) -> str:
    """Lightweight 100% offline plural stripper and stem normalizer."""
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    elif token.endswith("es") and len(token) > 3 and not token.endswith(("ss", "us", "is")):
        return token[:-2]
    elif token.endswith("s") and len(token) > 3 and not token.endswith("ss"):
        return token[:-1]
    return token


def tokenize_and_lemmatize(text: str) -> List[str]:
    """Tokenizes cleaned text, filters stopwords, and normalizes word forms."""
    cleaned = clean_text(text)
    tokens = cleaned.split()
    results: List[str] = []

    for token in tokens:
        if len(token) > 2 and token not in STOPWORDS and not token.isdigit():
            lemma = simple_lemmatize(token)
            results.append(lemma)

    return results


# ---------------------------------------------------------------------------
# F5: Local Keyword Extraction (TF-IDF + Term Salience, No External AI)
# ---------------------------------------------------------------------------

CUSTOMER_SALIENT_TERMS = {
    "payment", "refund", "charge", "order", "delivery", "shipping", "account",
    "login", "password", "transaction", "amount", "deducted", "failed", "money",
    "subscription", "cancel", "item", "damaged", "wrong", "delay", "service",
    "card", "bank", "fraud", "scam", "otp", "code", "phishing", "bug", "crash"
}


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """
    F5: Extracts the top 3-5 salient keywords from a conversation using term frequency and salience.
    100% local, zero latency, offline capable.
    """
    tokens = tokenize_and_lemmatize(text)
    if not tokens:
        return []

    # Count frequencies
    counts = Counter(tokens)

    # Score words: frequency * (2.0 if domain-salient else 1.0)
    scored = []
    for word, count in counts.items():
        if word in STOPWORDS or len(word) <= 2:
            continue
        weight = 2.0 if word in CUSTOMER_SALIENT_TERMS else 1.0
        score = count * weight
        scored.append((word, score))

    # Sort descending by score, then by original appearance
    scored.sort(key=lambda x: x[1], reverse=True)
    return [word for word, _ in scored[:top_n]]
