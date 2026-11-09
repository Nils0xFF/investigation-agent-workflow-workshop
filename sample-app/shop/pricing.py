"""Price parsing for the sample shop."""


def parse_amount(value: str) -> int:
    """Convert a storefront price string to cents. Prices are whole dollars, such as "12"."""
    return int(value) * 100


def order_subtotal(items: list[dict[str, str]]) -> int:
    """Return the subtotal of a cart in cents."""
    return sum(parse_amount(item["price"]) for item in items)
