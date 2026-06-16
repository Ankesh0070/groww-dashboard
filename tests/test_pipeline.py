import sys
import os

# Add src/ to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from core.scrubber import scrub_pii
from core.validator import validate_quote

def test_scrub_pii():
    # Test email masking
    assert scrub_pii("Contact me at test@example.com") == "Contact me at [EMAIL]"
    
    # Test phone masking
    assert scrub_pii("Call 123-456-7890 tomorrow") == "Call [PHONE] tomorrow"
    
    # Test ticket/ID masking
    assert scrub_pii("Ticket ID: 1234567") == "Ticket ID-[REDACTED]"
    assert scrub_pii("My transaction reference number is Txn:ABC12345") == "My transaction reference number is Txn-[REDACTED]"

def test_validate_quote():
    raw_reviews = [
        {"text": "The app freezes exactly when the market opens, very frustrating."},
        {"text": "I really like the simple UI and clean dashboard."}
    ]
    
    # Verbatim exact match
    assert validate_quote("freezes exactly when the market opens", raw_reviews) is True
    
    # Verbatim with capitalization difference and extra spaces (fuzzy matching)
    assert validate_quote("Freezes Exactly  When The Market Opens", raw_reviews) is True
    
    # Incorrect text (hallucinated)
    assert validate_quote("The app is totally broken and crashes on my phone", raw_reviews) is False
    
    # Short text (rejected to avoid trivial hits)
    assert validate_quote("good app", raw_reviews) is False

if __name__ == "__main__":
    print("Running local tests...")
    test_scrub_pii()
    test_validate_quote()
    print("All unit tests passed successfully!")
