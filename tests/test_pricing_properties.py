"""Property-based tests for inventory.pricing.

Tracked in GitHub issues #15 (compute_total linearity) and #17
(apply_discount monotonicity).
"""
from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from inventory.models import Order, Product
from inventory.pricing import apply_discount, compute_total


# --- Strategies ------------------------------------------------------------

# SKU: short non-empty ASCII identifier. Kept small so duplicates across
# items are likely (which is part of what we want to exercise).
sku_strategy = st.text(
    alphabet=st.characters(min_codepoint=65, max_codepoint=90),  # A-Z
    min_size=1,
    max_size=3,
)

# Prices: finite, non-negative, bounded so that price * qty * len(items)
# stays well away from float overflow.
price_strategy = st.floats(
    min_value=0.0,
    max_value=1_000_000.0,
    allow_nan=False,
    allow_infinity=False,
)

# Quantities: non-negative, bounded.
qty_strategy = st.integers(min_value=0, max_value=1_000)

# Discount percentages: finite, in [0, 100].
discount_strategy = st.floats(
    min_value=0.0,
    max_value=100.0,
    allow_nan=False,
    allow_infinity=False,
)


@st.composite
def catalog_and_order(draw):
    """Draw a catalog (dict[sku, Product]) and an Order whose items' SKUs
    are all drawn from the catalog. Duplicate SKUs in items are allowed.
    """
    # Non-empty catalog so we can always pick at least one SKU.
    skus = draw(st.lists(sku_strategy, min_size=1, max_size=5, unique=True))
    catalog = {
        sku: Product(sku=sku, name=sku, unit_price=draw(price_strategy))
        for sku in skus
    }

    # Order items: each picks a SKU from the catalog (duplicates allowed)
    # paired with a non-negative qty. Empty orders are valid too.
    items = draw(
        st.lists(
            st.tuples(st.sampled_from(skus), qty_strategy),
            min_size=0,
            max_size=20,
        )
    )
    order = Order(order_id="o", items=items)
    return catalog, order


# --- Property --------------------------------------------------------------

@given(catalog_and_order())
def test_compute_total_is_linear_when_discount_is_zero(pair):
    """compute_total(order, catalog, discount_pct=0) ==
    sum(catalog[sku].unit_price * qty for sku, qty in order.items).

    Holds for any catalog + order whose SKUs are all in the catalog, with
    duplicate SKUs allowed and quantities possibly zero.
    """
    catalog, order = pair
    expected = sum(
        catalog[sku].unit_price * qty for sku, qty in order.items
    )
    assert compute_total(order, catalog, discount_pct=0.0) == pytest.approx(
        expected
    )


@given(
    price=price_strategy,
    discounts=st.tuples(discount_strategy, discount_strategy),
)
def test_apply_discount_is_monotonic_in_discount_pct(price, discounts):
    """For any finite non-negative price and any d1 <= d2 in [0, 100]:

    - apply_discount(price, d1) >= apply_discount(price, d2)
    - the result is always in [0, price]
    """
    d1, d2 = sorted(discounts)

    p1 = apply_discount(price, d1)
    p2 = apply_discount(price, d2)

    # Monotonic: a larger discount yields a smaller-or-equal price.
    # Use a tiny absolute tolerance to absorb float rounding on equal inputs.
    assert p1 + 1e-9 >= p2

    # Bounded: result stays in [0, price] (again with a small tolerance
    # for floating-point noise at the endpoints).
    assert p1 >= -1e-9
    assert p2 >= -1e-9
    assert p1 <= price + 1e-9
    assert p2 <= price + 1e-9


@given(price=price_strategy)
def test_apply_discount_endpoint_identities(price):
    """d=0 returns the price unchanged; d=100 returns 0."""
    assert apply_discount(price, 0.0) == pytest.approx(price)
    assert apply_discount(price, 100.0) == pytest.approx(0.0)
