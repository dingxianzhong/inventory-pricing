"""Core domain objects."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Product:
    sku: str
    name: str
    unit_price: float
    weight_kg: float = 0.0

    def __post_init__(self):
        if self.unit_price < 0:
            raise ValueError("unit_price must be non-negative")


@dataclass
class Warehouse:
    """A named inventory container tracking per-SKU quantities.

    Note on zero-quantity SKUs:
        ``add(sku, 0)`` creates a ``stock`` entry with value 0 for a new
        SKU. ``remove(sku, qty)`` with ``qty > 0`` decrements the count
        down to zero and leaves the SKU in ``stock`` with value ``0``.
        This "present at 0" state is distinguishable from "absent SKU"
        and is observable via ``monthly_report`` and
        ``stock_alert(threshold=0)``. Whether to collapse the two states
        is tracked as a design decision in issue #21:
        https://github.com/dingxianzhong/inventory-pricing/issues/21
    """

    name: str
    stock: dict[str, int] = field(default_factory=dict)

    def add(self, sku: str, qty: int):
        self.stock[sku] = self.stock.get(sku, 0) + qty

    def remove(self, sku: str, qty: int) -> bool:
        """Remove qty units. Returns True if successful."""
        if self.stock.get(sku, 0) < qty:
            return False
        self.stock[sku] -= qty
        return True

    def available(self, sku: str) -> int:
        return self.stock.get(sku, 0)


@dataclass
class Order:
    order_id: str
    items: list[tuple[str, int]]  # (sku, qty)
    customer: str = ""

    def total_units(self) -> int:
        return sum(qty for _, qty in self.items)

    def is_empty(self) -> bool:
        return len(self.items) == 0
