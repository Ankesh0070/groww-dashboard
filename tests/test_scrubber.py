# pyrefly: ignore [missing-import]
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# pyrefly: ignore [missing-import]
from core.scrubber import scrub_pii

def test_scrub_email():
    text = "Contact me at user123@groww.in for help."
    result = scrub_pii(text)
    assert "user123@groww.in" not in result
    assert "[EMAIL]" in result

def test_scrub_phone():
    text = "Call +91-9876543210 right now!"
    result = scrub_pii(text)
    assert "+91-9876543210" not in result
    assert "[PHONE]" in result

def test_scrub_ids():
    text = "My ticket ID:123456 has been pending."
    result = scrub_pii(text)
    assert "ID:123456" not in result
    assert "ID-[REDACTED]" in result

def test_scrub_no_pii():
    text = "Great app, highly recommend."
    assert scrub_pii(text) == text
