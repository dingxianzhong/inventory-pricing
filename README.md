# inventory-pricing

[![CI](https://github.com/dingxianzhong/inventory-pricing/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/dingxianzhong/inventory-pricing/actions/workflows/ci.yml)

Toy inventory-management library.

## Install

```
pip install inventory-pricing
```

Heads-up: the **distribution name** (what you `pip install`) is
`inventory-pricing`, but the **import name** is plain `inventory`:

```python
from inventory.models import Product, Order
from inventory.pricing import compute_total
```

This split exists because `inventory` was already taken on PyPI by an
unrelated project. Distribution-name ≠ import-name is common in the
Python ecosystem (e.g. `pip install PyYAML` → `import yaml`).

## Layout

- `inventory/models.py` — Product, Warehouse, Order
- `inventory/pricing.py` — apply_discount, compute_total, bulk_price
- `inventory/reports.py` — stock_alert, monthly_report
- `tests/` — pytest tests
- `pyproject.toml` — package config

Run tests with:
```
python -m pytest tests/ -v
```

## Behavioral notes / breaking changes

- `inventory.pricing.compute_total` now **raises `KeyError` by default**
  when an order references a SKU that is not in the provided catalog.
  Previous (buggy) versions silently skipped unknown SKUs, which masked
  catalog-sync errors and produced under-priced totals.

  For migration, `compute_total` accepts a keyword-only
  `strict: bool = True` parameter. Passing `strict=False` restores the old
  lenient behavior (unknown SKUs silently skipped) and emits a
  `DeprecationWarning`. The `strict=False` option is a temporary migration
  aid and will be removed in a future release.

  **Preferred migration** — pre-filter `order.items` against the catalog
  and keep `strict=True` (the default):

  ```python
  from inventory.models import Order
  from inventory.pricing import compute_total

  known = [(sku, qty) for sku, qty in order.items if sku in catalog]
  filtered = Order(
      order_id=order.order_id,
      items=known,
      customer=order.customer,
  )
  total = compute_total(filtered, catalog, discount_pct=10.0)
  ```

  **Temporary escape hatch** — opt in to the legacy behavior and
  acknowledge the warning:

  ```python
  total = compute_total(order, catalog, discount_pct=10.0, strict=False)
  # -> emits DeprecationWarning; unknown SKUs skipped.
  ```

  The emitted warning message begins with the stable prefix:

  ```
  [inventory] compute_total(strict=False) is deprecated
  ```

  Downstream projects can match on that prefix to silence, escalate, or
  route the warning without scraping the full message. For example, to
  turn it into an error in your own test suite:

  ```python
  import warnings
  warnings.filterwarnings(
      "error",
      message=r"\[inventory\] compute_total\(strict=False\) is deprecated.*",
      category=DeprecationWarning,
  )
  ```

  or equivalently via pytest config:

  ```toml
  # pyproject.toml
  [tool.pytest.ini_options]
  filterwarnings = [
      "error:\\[inventory\\] compute_total\\(strict=False\\) is deprecated:DeprecationWarning",
  ]
  ```

  `strict=False` is deprecated in 2.0.0 and **scheduled for removal in
  3.0.0** (next major release); treat the warning as a hard deadline.

  Note: Python hides `DeprecationWarning` by default outside of `__main__`.
  To actually see the warning during development or CI, enable it with one
  of:

  - CLI: `python -W default::DeprecationWarning your_script.py`
  - Env var: `PYTHONWARNINGS=default::DeprecationWarning`
  - pytest: run with `-W default::DeprecationWarning` (or set
    `filterwarnings` in `pyproject.toml` / `pytest.ini`)
  - Programmatically:
    ```python
    import warnings
    warnings.filterwarnings("default", category=DeprecationWarning)
    ```
- `inventory.pricing.apply_discount` now **validates `discount_pct`** and
  raises `ValueError` if it is outside `[0, 100]` (or NaN). Because
  `compute_total` delegates to `apply_discount`, the same validation applies
  to its `discount_pct` argument.
- `inventory.models.Product` now **raises `ValueError`** on negative
  `unit_price` instead of silently clamping to 0.
- `inventory.reports.stock_alert` is **inclusive** of the threshold: a SKU
  with `qty == threshold` is reported.
- `inventory.pricing.bulk_price` applies the 10% discount at `qty >= 100`
  (boundary included).
