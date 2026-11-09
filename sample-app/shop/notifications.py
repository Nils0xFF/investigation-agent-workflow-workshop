"""Order confirmation emails."""

from dataclasses import dataclass


@dataclass
class Customer:
    name: str
    email: str


@dataclass
class Order:
    id: str
    total_cents: int
    # None for guest checkout: the shopper did not create an account.
    customer: Customer | None = None


def confirmation_recipient(order: Order) -> str:
    """Return the address the confirmation email goes to."""
    return order.customer.email


def send_confirmation(order: Order) -> str:
    """Pretend to send the confirmation email and return the recipient."""
    recipient = confirmation_recipient(order)
    return recipient
