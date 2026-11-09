"""The checkout flow, and the six scenarios that exercise it.

Each scenario is a realistic order that hits one of the sample shop's bugs. `send_error.py` runs them and sends the
exception to Sentry, so the investigation agent has something real to chase.
"""

from collections.abc import Callable

from shop import discounts, inventory, notifications, pricing, shipping, taxes


def scenario_decimal_price() -> None:
    """A poster priced "12.50" reaches checkout."""
    cart = [{"sku": "mug", "price": "12"}, {"sku": "poster", "price": "12.50"}]
    pricing.order_subtotal(cart)


def scenario_legacy_country_code() -> None:
    """A customer from the United Kingdom checks out with the legacy "UK" code."""
    shipping.rate_for("UK")


def scenario_empty_cart_discount() -> None:
    """A member applies a loyalty discount to a cart that was emptied in another tab."""
    discounts.loyalty_discount([], 0)


def scenario_warehouse_quantities() -> None:
    """A reservation checks the warehouse export, where quantities are text."""
    inventory.reserve("poster", 2)


def scenario_guest_confirmation() -> None:
    """A guest order has no customer record to email."""
    notifications.send_confirmation(notifications.Order(id="o-1042", total_cents=1200, customer=None))


def scenario_country_without_province() -> None:
    """A French order is taxed with the bare country code."""
    taxes.tax_for(1200, "FR")


SCENARIOS: dict[int, Callable[[], None]] = {
    1: scenario_decimal_price,
    2: scenario_legacy_country_code,
    3: scenario_empty_cart_discount,
    4: scenario_warehouse_quantities,
    5: scenario_guest_confirmation,
    6: scenario_country_without_province,
}
