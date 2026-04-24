"""Pricing utilities."""
from __future__ import annotations

import warnings

from .models import Order, Product


def apply_discount(price: float, discount_pct: float) -> float:
    """Apply a percentage discount to a price.

    Args:
        price: The pre-discount price.
        discount_pct: Percentage discount. Must be in the closed interval
            [0, 100]. ``0`` means no discount; ``100`` means free.

    Returns:
        ``price * (1 - discount_pct / 100)``.

    Raises:
        ValueError: If ``discount_pct`` is outside [0, 100] (including NaN).

    Note:
        ``compute_total`` delegates to this function, so the same validation
        applies to its ``discount_pct`` argument.
    """
    # Reject NaN and out-of-range values. The ``not (0 <= x <= 100)`` form
    # also catches NaN, since all comparisons with NaN are False.
    if not (0 <= discount_pct <= 100):
        raise ValueError(
            f"discount_pct must be in [0, 100], got {discount_pct!r}"
        )
    return price * (1 - discount_pct / 100)


def compute_total(
    order: Order,
    catalog: dict[str, Product],
    discount_pct: float = 0.0,
    *,
    strict: bool = True,
) -> float:
    """Compute the total price for an order, applying a discount.

    Args:
        order: The order to price.
        catalog: Mapping of SKU -> Product.
        discount_pct: Percentage discount in [0, 100] applied to the subtotal.
        strict: If ``True`` (default), unknown SKUs raise ``KeyError``. If
            ``False``, unknown SKUs are silently skipped and a
            ``DeprecationWarning`` is emitted. ``strict=False`` exists only as
            a migration aid for callers that relied on the old lenient
            behavior; it will be removed in a future release.

    Returns:
        The discounted total price.

    Raises:
        KeyError: If ``strict=True`` and any SKU in ``order.items`` is not
            present in ``catalog``.
        ValueError: If ``discount_pct`` is outside [0, 100] (validated by
            ``apply_discount``).

    Warns:
        DeprecationWarning: When ``strict=False`` is passed. The lenient
            behavior hides catalog-sync errors and produces under-priced
            totals; prefer pre-filtering ``order.items`` against ``catalog``::

                known = [
                    (sku, qty) for sku, qty in order.items
                    if sku in catalog
                ]
                filtered = Order(order_id=order.order_id, items=known,
                                 customer=order.customer)
                compute_total(filtered, catalog, discount_pct)
    """
    # TODO(#1): Remove the `strict` parameter in 3.0.0. See the tracking
    # issue for the full checklist (drop param, remove warning/tests/docs,
    # bump README/CHANGELOG):
    # https://github.com/dingxianzhong/inventory-pricing/issues/1
    if not strict:
        warnings.warn(
            "[inventory] compute_total(strict=False) is deprecated and will "
            "be removed in inventory 3.0.0: unknown SKUs are silently "
            "skipped, which can hide catalog-sync errors. Pre-filter "
            "order.items against catalog and use strict=True (the default) "
            "instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    subtotal = 0.0
    for sku, qty in order.items:
        product = catalog.get(sku)
        if product is None:
            if strict:
                raise KeyError(sku)
            continue
        subtotal += product.unit_price * qty
    return apply_discount(subtotal, discount_pct)


def bulk_price(product: Product, qty: int) -> float:
    """Compute total for qty units, with a 10% discount at 100+ units."""
    if qty >= 100:
        return product.unit_price * qty * 0.9
    return product.unit_price * qty
