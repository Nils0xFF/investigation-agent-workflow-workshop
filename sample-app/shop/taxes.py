"""Sales tax by region."""

# Region codes are "<country>-<province>", such as "CA-ON". Countries without provinces are listed on their own.
TAX_RATES = {"CA-ON": 0.13, "CA-QC": 0.14975, "FR": 0.20, "DE": 0.19}


def rate_for_region(region: str) -> float:
    """Return the tax rate for a region code such as "CA-ON"."""
    country, province = region.split("-")[0], region.split("-")[1]
    return TAX_RATES[f"{country}-{province}"]


def tax_for(subtotal_cents: int, region: str) -> int:
    """Return the tax due on a subtotal, in cents."""
    return round(subtotal_cents * rate_for_region(region))
