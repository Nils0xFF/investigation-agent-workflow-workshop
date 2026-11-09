"""Loyalty discounts."""


def average_item_price(items: list[dict[str, str]], subtotal_cents: int) -> int:
    """Return the average price of the items in a cart, in cents."""
    return subtotal_cents // len(items)


def loyalty_discount(items: list[dict[str, str]], subtotal_cents: int) -> int:
    """Members get 10% off carts whose average item price is above 20.00."""
    if average_item_price(items, subtotal_cents) > 2000:
        return subtotal_cents // 10
    return 0
