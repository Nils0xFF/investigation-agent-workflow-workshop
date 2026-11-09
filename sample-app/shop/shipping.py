"""Flat shipping rates by destination country."""

# ISO 3166-1 alpha-2 codes. The storefront was migrated from a legacy system that used "UK" for the United Kingdom.
RATES_CENTS = {"FR": 590, "DE": 690, "GB": 790, "ES": 690, "IT": 690}


def rate_for(country: str) -> int:
    """Return the shipping rate in cents for a destination country code."""
    return RATES_CENTS[country]
