"""Property-based tests for inventory.models.

Tracked in GitHub issue #18.
"""
from __future__ import annotations

from copy import deepcopy

from hypothesis import given
from hypothesis import strategies as st

from inventory.models import Warehouse

# --- Strategies ------------------------------------------------------------

# Small SKU alphabet so the generated SKU often collides with the initial
# stock keys (exercising the "existing SKU" case), but also sometimes
# doesn't (exercising the "new SKU" case).
sku_strategy = st.text(
    alphabet=st.characters(min_codepoint=65, max_codepoint=70),  # A-F
    min_size=1,
    max_size=2,
)

# Non-negative integer quantities. Includes 0 so the no-op/identity case
# is exercised.
qty_strategy = st.integers(min_value=0, max_value=1_000)

# Initial stock: a dict[sku, non-negative int]. May be empty.
stock_strategy = st.dictionaries(
    keys=sku_strategy,
    values=qty_strategy,
    max_size=5,
)


# --- Properties ------------------------------------------------------------

@st.composite
def stock_and_existing_sku(draw):
    """Draw a non-empty stock dict and a SKU that is guaranteed to be one
    of its existing keys. Lets us state a clean identity property for the
    "existing SKU" case.
    """
    stock = draw(stock_strategy.filter(lambda s: len(s) > 0))
    sku = draw(st.sampled_from(sorted(stock)))
    return stock, sku


@given(pair=stock_and_existing_sku(), qty=qty_strategy)
def test_add_then_remove_is_identity_for_existing_sku(pair, qty):
    """For any starting stock, any SKU **already present** in that stock,
    and any qty >= 0:

    1. ``add(sku, qty)`` then ``remove(sku, qty)`` leaves the stock exactly
       equal to the initial stock.
    2. ``remove`` returns ``True``.

    Covers qty=0 (pure no-op) and qty>0 (round-trip) on existing SKUs.
    """
    initial_stock, sku = pair
    # Warehouse mutates its own dict in place, so snapshot the expected
    # value from a deep copy before handing another copy to the Warehouse.
    expected = deepcopy(initial_stock)
    w = Warehouse(name="w", stock=deepcopy(initial_stock))

    w.add(sku, qty)
    removed_ok = w.remove(sku, qty)

    assert removed_ok is True
    assert w.stock == expected


@given(initial_stock=stock_strategy, sku=sku_strategy, qty=qty_strategy)
def test_add_then_remove_preserves_effective_stock(initial_stock, sku, qty):
    """Weaker "effective stock" property that holds for ANY SKU (existing
    or new): after ``add(sku, qty)`` + ``remove(sku, qty)``, the stock
    agrees with the initial stock on every SKU's quantity, treating a
    missing SKU as 0. ``remove`` always returns ``True``.

    This is the honest statement of the round-trip invariant on the
    current API: ``remove`` does not delete a SKU when its count hits 0,
    so a brand-new SKU passed to ``add(sku, n)`` + ``remove(sku, n)`` is
    left behind as ``{sku: 0}``. Quantities are unchanged in every
    observable sense (``available(sku) == initial_stock.get(sku, 0)``).
    """
    w = Warehouse(name="w", stock=deepcopy(initial_stock))

    w.add(sku, qty)
    removed_ok = w.remove(sku, qty)

    assert removed_ok is True
    # Every SKU that was in initial_stock retains its original quantity.
    for k, v in initial_stock.items():
        assert w.available(k) == v
    # The possibly-newly-introduced SKU is observable as 0 (i.e. absent
    # for all practical purposes).
    assert w.available(sku) == initial_stock.get(sku, 0)
