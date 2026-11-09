"""The six planted bugs stay in place: each scenario raises the exception the evals expect."""

import pytest

from shop import checkout
from shop.checkout import SCENARIOS

EXPECTED = {
    1: ValueError,
    2: KeyError,
    3: ZeroDivisionError,
    4: TypeError,
    5: AttributeError,
    6: IndexError,
}


def test_there_are_six_scenarios() -> None:
    assert sorted(SCENARIOS) == sorted(EXPECTED)


@pytest.mark.parametrize(("number", "exception"), sorted(EXPECTED.items()))
def test_each_scenario_raises_its_exception(number: int, exception: type[Exception]) -> None:
    with pytest.raises(exception):
        SCENARIOS[number]()


def test_the_happy_paths_still_work() -> None:
    # The bugs are edge cases: ordinary orders go through, so the agent must explain which input breaks the assumption.
    assert checkout.pricing.order_subtotal([{"sku": "mug", "price": "12"}]) == 1200
    assert checkout.shipping.rate_for("GB") == 790
    assert checkout.discounts.loyalty_discount([{"sku": "lamp", "price": "30"}], 3000) == 300
    checkout.inventory.reserve("poster", 2, stock={"poster": 3})
    assert checkout.notifications.send_confirmation(checkout.notifications.Order(id="o-1", total_cents=1, customer=checkout.notifications.Customer("Ada", "ada@example.com"))) == "ada@example.com"
    assert checkout.taxes.tax_for(1000, "CA-ON") == 130
