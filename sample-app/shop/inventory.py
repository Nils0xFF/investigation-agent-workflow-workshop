"""Stock levels, loaded from the warehouse export."""

import csv
import io

# A snapshot of the warehouse CSV export. Every column is text, including quantities.
WAREHOUSE_EXPORT = """sku,quantity
mug,12
poster,3
tote,0
"""


def load_stock() -> dict[str, str]:
    """Return the stock level of every SKU as exported by the warehouse."""
    return {row["sku"]: row["quantity"] for row in csv.DictReader(io.StringIO(WAREHOUSE_EXPORT))}


def reserve(sku: str, quantity: int, stock: dict[str, str] | None = None) -> None:
    """Reserve `quantity` units of `sku`, failing when there is not enough stock."""
    levels = stock if stock is not None else load_stock()
    if levels[sku] < quantity:
        raise RuntimeError(f"Not enough stock for {sku}")
