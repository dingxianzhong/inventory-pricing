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
