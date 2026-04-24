"""A toy inventory management library."""

from .models import Product, Warehouse, Order
from .pricing import apply_discount, compute_total
from .reports import monthly_report, stock_alert

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Product",
    "Warehouse",
    "Order",
    "apply_discount",
    "compute_total",
    "monthly_report",
    "stock_alert",
]
