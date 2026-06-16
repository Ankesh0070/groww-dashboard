# pyrefly: ignore [missing-import]
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# pyrefly: ignore [missing-import]
from core.validator import validate_quote

def test_validate_quote_exact_match():
    raw_reviews = [{"text": "The app is fantastic for trading options."}]
    assert validate_quote("The app is fantastic for trading options.", raw_reviews) is True

def test_validate_quote_substring_match():
    raw_reviews = [{"text": "I really think the app is fantastic for trading options, especially for beginners."}]
    assert validate_quote("the app is fantastic for trading options", raw_reviews) is True

def test_validate_quote_hallucinated():
    raw_reviews = [{"text": "I really think the app is fantastic."}]
    assert validate_quote("The app is fantastic for trading options", raw_reviews) is False

def test_validate_quote_too_short():
    # Quotes with < 3 standard words should be rejected to avoid trivial false positives
    raw_reviews = [{"text": "good app"}]
    assert validate_quote("good", raw_reviews) is False
