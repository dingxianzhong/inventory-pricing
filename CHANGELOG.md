# Changelog

All notable changes to this project are documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Tests: property-based coverage (`tests/test_*_properties.py`) for
  pricing, reports, and models invariants using Hypothesis.
  Covers `compute_total` linearity, `apply_discount` monotonicity and
  endpoint identities, `monthly_report` distributivity over partitions
  and order-independence, and `Warehouse.add` + `remove` round-trips.
  Also pins `monthly_report`'s zero-quantity SKU preservation behavior
  with targeted regression tests. See PR #22.
- CI: `lint` job (ruff + flake8) and `typecheck` job (mypy) running in
  parallel with the existing test matrix. Tool versions pinned via the
  new `lint` and `typecheck` optional-dependency extras in
  `pyproject.toml`. Pre-commit config (`ruff --fix`, flake8,
  `end-of-file-fixer`, `trailing-whitespace`) and contributor docs
  added. See PRs #23, #24.

## [0.1.2rc1] - 2026-04-24

Pre-release on TestPyPI only. First release cut via PyPI Trusted
Publishing (OIDC) instead of long-lived API tokens; no code changes
from 0.1.1. Purpose is to verify the migration landed in #6 works
end-to-end before removing the `PYPI_API_TOKEN` / `TEST_PYPI_API_TOKEN`
secrets and closing #3.

### Changed

- Release workflow now authenticates to PyPI / TestPyPI via OIDC
  Trusted Publishing; no repo-level publish token is required. See
  `CONTRIBUTING.md` → Releases and PR #6.

## [0.1.1] - 2026-04-24

### Changed

- `inventory.__version__` is now sourced at import time from
  `importlib.metadata.version("inventory-pricing")` instead of being
  hard-coded in `inventory/__init__.py`. `pyproject.toml` is now the
  single source of truth for the version string; drift between the two
  is structurally impossible. For uninstalled source checkouts (where
  the distribution isn't registered with `importlib.metadata`),
  `__version__` falls back to the sentinel `"0.0.0+local"` so imports
  never fail. See issue #2.

## [2.0.0] - 2026-04-24

This is a major release with intentional breaking changes. Downstream
users should read the "Migration guide" section below and the
"Behavioral notes / breaking changes" section of `README.md` before
upgrading.

### Deprecated

- **`compute_total(..., strict=False)`** is deprecated as of 2.0.0 and
  is **scheduled for removal in 3.0.0** (target timeline: next major
  release). Passing `strict=False` currently emits a
  `DeprecationWarning` whose message begins with the stable prefix
  `[inventory] compute_total(strict=False) is deprecated` so downstream
  projects can filter on it. Migrate to pre-filtering `order.items`
  against the catalog and keeping the default `strict=True`; see
  `README.md` for the snippet.

### Changed (behavioral / breaking)

- **`inventory.pricing.compute_total`** now raises `KeyError` by default
  when an order references a SKU that is not present in the catalog.
  Previous versions silently skipped unknown SKUs, which masked
  catalog-sync errors and produced under-priced totals.
  - A keyword-only `strict: bool = True` parameter was added. Passing
    `strict=False` restores the old lenient behavior and emits a
    `DeprecationWarning`. `strict=False` is a temporary migration aid
    and will be removed in **3.0.0** (see "Deprecated" above). See
    `README.md` for the recommended pre-filtering migration snippet and
    for how to surface the `DeprecationWarning` (which Python hides by
    default).
- **`inventory.pricing.apply_discount`** now validates `discount_pct` and
  raises `ValueError` if it is outside `[0, 100]` (NaN is also rejected).
  Because `compute_total` delegates to `apply_discount`, the same
  validation applies to its `discount_pct` argument.
- **`inventory.models.Product`** now raises `ValueError` on a negative
  `unit_price` instead of silently clamping it to `0.0`.
- **`inventory.reports.stock_alert`** is now inclusive of the threshold:
  a SKU with `qty == threshold` is reported. Previously only strict
  less-than triggered an alert.
- **`inventory.pricing.bulk_price`** applies the 10% bulk discount at
  `qty >= 100` (boundary included). The previous threshold direction was
  inverted.

### Fixed

- `inventory.models.Warehouse.add` no longer raises `KeyError` when
  adding stock for a SKU that isn't already in the warehouse; it now
  initializes missing entries to `0` before incrementing.
- `inventory.models.Order.total_units` now sums quantities directly
  instead of doubling them (leftover from an old pricing-per-pair
  feature).
- `inventory.models.Order.is_empty` now reflects whether `items` is
  empty, rather than whether the (doubled) unit count happened to be
  zero. Orders containing zero-quantity line items are no longer
  reported as empty.
- `inventory.reports.monthly_report` now accumulates quantities across
  warehouses per SKU instead of overwriting, so totals reflect the sum
  across all warehouses.
- `inventory.pricing.apply_discount` now treats `discount_pct` as a
  percentage in `[0, 100]` rather than as a fraction in `[0, 1]`.

### Added

- `inventory.__version__` attribute (set to `"2.0.0"`), re-exported
  from the package root and listed in `__all__`.
- `strict` keyword-only parameter on `compute_total` (see above).
- Input validation on `apply_discount` / `compute_total` for
  `discount_pct`.
- Boundary-case tests:
  - `bulk_price` at `qty == 99`, `100`, `101`.
  - `stock_alert` at `qty == threshold - 1`, `threshold`, `threshold + 1`.
  - `apply_discount` with negative, `> 100`, `NaN`, and exact-boundary
    discount percentages.
  - `compute_total` with `strict=False` (skip + warn), with
    `strict=True` (no warning), and with invalid `discount_pct`.

### Migration guide

See the "Behavioral notes / breaking changes" section of `README.md`
for the pre-filtering snippet for `compute_total` and for instructions
on surfacing the new `DeprecationWarning` during development and CI.
