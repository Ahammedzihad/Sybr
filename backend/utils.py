"""
PII masking utilities for conversation data.
"""

import re


def mask_pii(text: str) -> str:
    """
    Masks PII elements from text:
    - Masks email addresses using regex, replacing the local part but keeping the domain
      (e.g., 'john.doe@company.com' becomes '***@company.com').
    - Masks phone-number-like digit sequences of 7+ digits with '***-****'.
    - Returns the masked text.
    """
    if not text:
        return ""

    # 1. Mask emails: retain domain, mask mailbox prefix
    email_pattern = r'[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})'
    masked = re.sub(email_pattern, r'***@\1', text)

    # 2. Mask phone numbers: 7 or more digits with optional dashes, parens, spaces
    phone_pattern = r'(?:\+?\d{1,3}[\s.-]*)?(?:\(\d{1,4}\)[\s.-]*)?\d(?:[\s.-]*\d){6,}'
    masked = re.sub(phone_pattern, '***-****', masked)

    return masked
