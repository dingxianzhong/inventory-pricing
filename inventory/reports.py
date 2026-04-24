"""Report generation."""
from __future__ import annotations

from .models import Warehouse


def stock_alert(warehouse: Warehouse, threshold: int = 10) -> list[str]:
    """Return SKUs with stock at or below threshold."""
    return [sku for sku, qty in warehouse.stock.items() if qty <= threshold]


def monthly_report(warehouses: list[Warehouse]) -> dict[str, int]:
    """Aggregate stock across warehouses by SKU."""
    totals: dict[str, int] = {}
    for w in warehouses:
        for sku, qty in w.stock.items():
            totals[sku] = totals.get(sku, 0) + qty
    return totals
