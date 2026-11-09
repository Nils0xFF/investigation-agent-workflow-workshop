"""Shared test setup: placeholder credentials and connector names, so no test needs a Studio workspace or network.

The connector names mimic the unique names Studio gives connectors. They are set before any test imports agent/main.py.
"""

import json
import os

import pytest

os.environ.setdefault("SENTRY_CONNECTOR_NAME", "sentry_a1b2")
os.environ.setdefault("GITHUB_CONNECTOR_NAME", "github_app")
os.environ.setdefault("MISTRAL_API_KEY", "test-key")
# A placeholder deployment name keeps the workflows SDK from asking for one at import time.

# A complete, valid report the scripted model can answer with.
VALID_REPORT = {
    "summary": "Checkout fails for United Kingdom orders because the shipping table has no 'UK' entry.",
    "exception": "KeyError: 'UK'",
    "file": "sample-app/shop/shipping.py",
    "symbol": "rate_for",
    "root_cause": "rate_for looks the legacy 'UK' country code up in RATES_CENTS, which only has the ISO code 'GB': `return RATES_CENTS[country]`.",
    "confidence": "high",
    "evidence": [
        {"source": "sentry", "reference": "https://sentry.io/organizations/acme/issues/1", "proves": "KeyError: 'UK' raised in shop/shipping.py rate_for"},
        {"source": "github", "reference": "https://github.com/acme/shop/blob/abc123/sample-app/shop/shipping.py", "proves": "RATES_CENTS has GB, not UK"},
    ],
    "next_check": None,
}


@pytest.fixture
def valid_report_json() -> str:
    return json.dumps(VALID_REPORT)
