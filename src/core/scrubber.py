import re

# Regex patterns for various PII types
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
)

# Matches standard phone number formats: +1-123-456-7890, (123) 456-7890, 10-digit numbers, etc.
PHONE_REGEX = re.compile(
    r"\+?\b\d{1,4}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"
)

# Generic pattern for account numbers, customer IDs or transaction references (requires at least one digit)
ID_REGEX = re.compile(
    r"\b(acc|id|txn|ref|order|user|cust|ticket)[\s:-]+[a-zA-Z0-9]*[0-9]+[a-zA-Z0-9]*\b",
    re.IGNORECASE
)

def scrub_pii(text: str) -> str:
    """
    Sanitizes review text by masking sensitive information like email addresses,
    phone numbers, and account/transaction IDs.
    """
    if not text:
        return ""
    
    # 1. Mask Email Addresses
    text = EMAIL_REGEX.sub("[EMAIL]", text)
    
    # 2. Mask Phone Numbers
    text = PHONE_REGEX.sub("[PHONE]", text)
    
    # 3. Mask Account/Transaction IDs
    text = ID_REGEX.sub(r"\1-[REDACTED]", text)
    
    return text
