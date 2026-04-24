"""A toy inventory management library."""

from importlib.metadata import PackageNotFoundError, version as _dist_version

from .models import Product, Warehouse, Order
from .pricing import apply_discount, compute_total
from .reports import monthly_report, stock_alert

# Source __version__ from installed distribution metadata so it can't
# drift from pyproject.toml. Distribution name is `inventory-pricing`
# (hyphen); the import package is `inventory`. See issue #2.
try:
    __version__ = _dist_version("inventory-pricing")
except PackageNotFoundError:
    # Source checkout / editable install before `pip install -e .` has
    # registered the dist, or running straight from the repo with no
    # install at all. Keep a sentinel so `inventory.__version__` is
    # always a string — downstream code that treats it as such won't
    # blow up during local development.
    __version__ = "0.0.0+local"

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
