"""
Security Preprocessing & Text Normalization Module.
Strips HTML, email artifacts, normalizes unicode, handles edge cases,
and demonstrates spaCy tokenization and light stopword filtering for downstream AI.
"""

import html
import json
import logging
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

import spacy

logger = logging.getLogger(__name__)

# Lazy-loaded spaCy NLP model
_nlp = None

# Critical words that must NEVER be removed as stopwords to preserve
# security semantics, negations, urgency, and customer intent.
PRESERVED_SEMANTIC_WORDS = {
    "not", "no", "never", "none", "neither", "nor", "cannot", "without",
    "against", "under", "within", "now", "before", "after", "urgent",
    "password", "login", "verify", "otp", "code", "account", "suspended",
}

# Regex patterns for email and chat cleaning
HTML_TAG_RE = re.compile(r"<[^>]+>")
FORWARDED_HEADER_RE = re.compile(
    r"^[-_\s]*(?:forwarded message|original message)[-_\s]*\n?"
    r"|(?:^|\n)(?:from|to|sent|date|subject):\s+[^\n]+",
    re.IGNORECASE | re.MULTILINE
)
QUOTED_LINE_RE = re.compile(r"^\s*(?:>|&gt;|\|)+.*$", re.MULTILINE)
SIGNATURE_BLOCK_RE = re.compile(
    r"(?:sent from my (?:iphone|ipad|android|samsung|galaxy|mobile|device)[^\n]*)"
    r"|(?:--\s*\n.*)"
    r"|^\s*(?:best regards|warm regards|kind regards|sincerely|cheers|thanks & regards|thanks and regards)\s*,?.*$",
    re.IGNORECASE | re.MULTILINE
)
EXCESSIVE_SPACE_RE = re.compile(r"\s+")


def get_spacy_model():
    """Lazily load and return the spaCy en_core_web_sm pipeline."""
    global _nlp
    if _nlp is None:
        try:
            # Disable unnecessary parser/NER components for maximum preprocessing speed
            _nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
        except Exception as e:
            logger.warning("Falling back to basic English spacy model: %s", e)
            _nlp = spacy.blank("en")
    return _nlp


def preprocess(text: Optional[str], light_stopwords: bool = True) -> str:
    """
    Cleans and normalizes raw text for downstream AI threat analysis.

    1. Cleaning:
       - Strips HTML tags and decodes HTML entities
       - Strips email artifacts (forwarded headers, signatures, quote lines)
       - Normalizes unicode (NFKC) while safely retaining currency symbols, emojis, and quotes
       - Collapses excessive whitespace and newlines
    2. Tokenization:
       - Uses spaCy to tokenize the cleaned text
    3. NLP processing:
       - Performs light stopword filtering using spaCy's token.is_stop,
         preserving critical negation, security, and sentiment words
    4. Edge cases:
       - None, empty strings, non-English text, and pure junk return "" safely without crashing.

    Returns:
        Cleaned, readable string suitable for downstream AI analysis.
    """
    # Edge case: None or non-string input
    if text is None or not isinstance(text, str):
        return ""

    # Edge case: purely empty or whitespace string
    raw = text.strip()
    if not raw:
        return ""

    # 1. Cleaning
    # Replace HTML block/break tags with newlines so line-based email artifact patterns work
    clean = re.sub(r"(?i)</?(?:p|div|br|li|tr|h\d)[^>]*>", "\n", raw)
    clean = HTML_TAG_RE.sub(" ", clean)
    clean = html.unescape(clean)

    # Strip forwarded headers and quoted replies
    clean = FORWARDED_HEADER_RE.sub("\n", clean)
    clean = QUOTED_LINE_RE.sub("\n", clean)

    # Strip signature blocks
    clean = SIGNATURE_BLOCK_RE.sub("\n", clean)

    # Unicode normalization (NFKC) - normalizes smart quotes, accents, preserves currencies & emojis
    clean = unicodedata.normalize("NFKC", clean)

    # Normalize specific smart punctuation to standard ASCII quotes
    clean = clean.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

    # Collapse excessive whitespace and newlines
    clean = EXCESSIVE_SPACE_RE.sub(" ", clean).strip()

    # Edge case: If text was entirely HTML/junk with no real content
    if not clean:
        return ""

    # 2. Tokenization via spaCy
    nlp = get_spacy_model()
    if len(clean) > nlp.max_length:
        nlp.max_length = len(clean) + 1_000_000
    doc = nlp(clean)

    # 3. Basic NLP processing: demonstrable tokenization and light stopword filtering
    # Tokens are extracted and inspected against spaCy's built-in stopword list
    processed_tokens: List[str] = []
    for token in doc:
        # Check if token is a stopword according to spaCy
        if light_stopwords and token.is_stop:
            lower_txt = token.text.lower()
            # Preserve critical semantic qualifiers (negations, urgency, security nouns)
            if lower_txt in PRESERVED_SEMANTIC_WORDS:
                processed_tokens.append(token.text)
            else:
                # Omit high-noise structural stopwords (e.g. "the", "a", "an", "is", "of")
                continue
        else:
            if not token.is_space:
                processed_tokens.append(token.text)

    # If all tokens were filtered out (pure stopword/punctuation junk), fallback safely
    if not processed_tokens:
        return clean

    # Reconstruct clean, readable text preserving proper punctuation spacing
    result_text = " ".join(processed_tokens)
    # Fix spacing before common punctuation marks
    result_text = re.sub(r'\s+([,.\?!:;])', r'\1', result_text)
    result_text = re.sub(r'\(\s+', '(', result_text)
    result_text = re.sub(r'\s+\)', ')', result_text)

    return result_text.strip()


def preprocess_batch(conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Runs preprocess() across every message in each conversation and adds
    a `clean_text` field to each conversation entry and message object.
    """
    processed_list = []
    for conv in conversations:
        # Create a shallow/deep copy to avoid mutating external references
        conv_copy = dict(conv)
        messages = conv_copy.get("messages", [])
        cleaned_msgs = []
        conversation_clean_parts = []

        for msg in messages:
            msg_copy = dict(msg)
            raw_text = msg_copy.get("text", "")
            cleaned = preprocess(raw_text)
            msg_copy["clean_text"] = cleaned
            cleaned_msgs.append(msg_copy)
            if cleaned:
                conversation_clean_parts.append(cleaned)

        conv_copy["messages"] = cleaned_msgs
        conv_copy["clean_text"] = " | ".join(conversation_clean_parts)
        processed_list.append(conv_copy)

    return processed_list


def main():
    """
    Runs batch preprocessing on dataset.json, outputs dataset_clean.json,
    and displays before/after verification examples.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    # Locate dataset.json in current directory, backend, or parent
    search_paths = [
        Path("dataset.json"),
        Path("backend/dataset.json"),
        Path(__file__).resolve().parent.parent.parent / "dataset.json",
        Path(__file__).resolve().parent.parent / "dataset.json",
    ]
    dataset_file = None
    for p in search_paths:
        if p.exists():
            dataset_file = p
            break

    if not dataset_file:
        print("ERROR: dataset.json not found. Please run load_dataset.py first.")
        sys.exit(1)

    print(f"Loading conversations from {dataset_file}...")
    with open(dataset_file, "r", encoding="utf-8") as f:
        conversations = json.load(f)

    # Run batch preprocessing
    cleaned_conversations = preprocess_batch(conversations)

    # Save to dataset_clean.json in working directory and backend directory
    out_paths = [Path("dataset_clean.json")]
    if Path("backend").exists() and Path("backend").is_dir():
        out_paths.append(Path("backend/dataset_clean.json"))

    for out_path in out_paths:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_conversations, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(cleaned_conversations)} preprocessed conversations to {out_path}")

    # Display before / after examples to confirm cleaning
    print("\n" + "=" * 75)
    print("        PREPROCESSING VERIFICATION: BEFORE vs. AFTER EXAMPLES       ")
    print("=" * 75)

    sample_count = 0
    for conv in cleaned_conversations:
        for msg in conv.get("messages", []):
            raw = msg.get("text", "")
            clean = msg.get("clean_text", "")
            if raw != clean and len(raw) > 20:
                sample_count += 1
                print(f"\n[Example {sample_count}] Conversation: {conv.get('conversation_id')} ({msg.get('sender')})")
                print("-" * 75)
                print(f"BEFORE (Raw):\n{raw}")
                print(f"\nAFTER (Cleaned):\n{clean}")
                print("-" * 75)
                if sample_count >= 5:
                    break
        if sample_count >= 5:
            break

    # Edge cases verification demonstration
    print("\n" + "=" * 75)
    print("               EDGE CASES VERIFICATION TEST RESULTS                ")
    print("=" * 75)
    edge_cases = [
        ("None input", None),
        ("Empty string", ""),
        ("Only whitespace", "    \n\t  "),
        ("Pure HTML tags", "<div><p><br/></p></div>"),
        ("Non-English text (French)", "Bonjour, mon colis n'est pas encore arrivé. Merci!"),
        ("Non-English text (Hindi)", "नमस्ते, मुझे अपना ऑर्डर कैंसिल करना है।"),
        ("Currency & Emojis", "Refund ₹2,500 and $50.00 right now! 😡🙏"),
        ("Email Artifacts", "Sent from my iPhone\nBest regards,\nJohn Doe"),
    ]

    for name, test_val in edge_cases:
        res = preprocess(test_val)
        print(f"  * {name:<30} -> Input: {repr(test_val)[:35]:<37} | Output: {repr(res)}")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
