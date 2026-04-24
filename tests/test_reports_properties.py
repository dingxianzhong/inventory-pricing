"""Property-based tests for inventory.reports.

Tracked in GitHub issue #16.
"""
from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from inventory.models import Warehouse
from inventory.reports import monthly_report

# --- Strategies ------------------------------------------------------------

# Small SKU alphabet so warehouses are likely to share SKUs (that's what
# makes aggregation interesting — pure disjoint stock would be a weaker
# test of distributivity).
sku_strategy = st.text(
    alphabet=st.characters(min_codepoint=65, max_codepoint=70),  # A-F
    min_size=1,
    max_size=2,
)

# Non-negative integer stock. Bounded so generated lists stay small.
qty_strategy = st.integers(min_value=0, max_value=1_000)

stock_strategy = st.dictionaries(
    keys=sku_strategy,
    values=qty_strategy,
    max_size=5,
)


@st.composite
def warehouse_strategy(draw):
    # Warehouse.name doesn't affect monthly_report, so just use an index-y
    # label to aid shrinking readability.
    stock = draw(stock_strategy)
    return Warehouse(name="w", stock=stock)


warehouses_strategy = st.lists(warehouse_strategy(), min_size=0, max_size=5)


# --- Helper ----------------------------------------------------------------

def _pointwise_sum(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    """Per-key sum of two SKU totals dicts, preserving ALL keys including
    those whose combined value is 0. Unlike ``Counter.__add__``, this does
    not drop non-positive totals — matching ``monthly_report``'s behavior.
    """
    result: dict[str, int] = dict(a)
    for sku, qty in b.items():
        result[sku] = result.get(sku, 0) + qty
    return result


# --- Properties ------------------------------------------------------------

@given(data=st.data())
def test_monthly_report_distributes_over_partitions(data):
    """For any list of warehouses `ws` and any index `i` in [0, len(ws)],
    monthly_report(ws) == pointwise_sum(
        monthly_report(ws[:i]), monthly_report(ws[i:])
    ).
    """
    ws = data.draw(warehouses_strategy, label="warehouses")
    i = data.draw(st.integers(min_value=0, max_value=len(ws)), label="split")

    left = monthly_report(ws[:i])
    right = monthly_report(ws[i:])
    combined = monthly_report(ws)

    assert combined == _pointwise_sum(left, right)


@given(warehouses_strategy)
def test_monthly_report_is_order_independent(ws):
    """monthly_report must not depend on the order of warehouses in the
    input list (aggregation is commutative).
    """
    assert monthly_report(ws) == monthly_report(list(reversed(ws)))
