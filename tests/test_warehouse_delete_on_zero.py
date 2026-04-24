"""Tests for the experimental Warehouse(delete_on_zero=...) flag.

See issue #21 for the design discussion. These tests exercise the
opt-in behavior (delete the SKU from stock when remove takes the
count to zero). Default-off behavior is already covered by the
existing Warehouse tests in test_models.py.
"""
from __future__ import annotations

from inventory.models import Warehouse

# --- Opt-in (delete_on_zero=True) -----------------------------------------


def test_remove_to_zero_deletes_key_when_flag_enabled():
    w = Warehouse(name="w", stock={"A": 3}, delete_on_zero=True)
    assert w.remove("A", 3) is True
    assert "A" not in w.stock
    assert w.stock == {}


def test_add_then_remove_new_sku_leaves_it_absent_when_flag_enabled():
    """The round-trip invariant the strengthened Option A would enable:
    add(new_sku, n) + remove(new_sku, n) is a true no-op on stock.
    """
    w = Warehouse(name="w", delete_on_zero=True)
    w.add("NEW", 5)
    assert w.remove("NEW", 5) is True
    assert "NEW" not in w.stock
    assert w.stock == {}


def test_add_then_remove_existing_sku_restores_exactly_when_flag_enabled():
    """Strict identity on pre-existing SKUs: the starting stock is
    restored byte-for-byte, and the SKU is NOT spuriously deleted
    just because it touched zero transiently during the round-trip.

    (It doesn't touch zero here — we add first, then remove — but
    this test pins the expectation that delete_on_zero doesn't affect
    SKUs whose final count is positive.)
    """
    w = Warehouse(name="w", stock={"A": 4, "B": 1}, delete_on_zero=True)
    w.add("A", 2)
    assert w.remove("A", 2) is True
    assert w.stock == {"A": 4, "B": 1}


def test_remove_to_positive_does_not_delete_key_when_flag_enabled():
    """Only the exact-to-zero case triggers deletion; positive residue
    leaves the key untouched.
    """
    w = Warehouse(name="w", stock={"A": 5}, delete_on_zero=True)
    assert w.remove("A", 2) is True
    assert w.stock == {"A": 3}


def test_flag_enabled_does_not_affect_insufficient_remove():
    """remove returns False when stock is too low; dict is unchanged
    regardless of the flag.
    """
    w = Warehouse(name="w", stock={"A": 2}, delete_on_zero=True)
    assert w.remove("A", 5) is False
    assert w.stock == {"A": 2}


def test_flag_enabled_does_not_affect_remove_from_missing_sku():
    w = Warehouse(name="w", delete_on_zero=True)
    assert w.remove("A", 1) is False
    assert w.stock == {}
    assert "A" not in w.stock


def test_flag_enabled_does_not_change_add_behavior():
    """add(sku, 0) still creates a {sku: 0} entry even with the flag on
    — the flag is scoped to remove's post-condition, not add's.
    """
    w = Warehouse(name="w", delete_on_zero=True)
    w.add("A", 0)
    assert w.stock == {"A": 0}
    assert "A" in w.stock


# --- Default (delete_on_zero=False) — sanity regression -------------------


def test_default_flag_value_is_false():
    """The default must remain False so that pre-flag callers see no
    behavior change. Pinning this explicitly so a later bump of the
    default is an obvious, deliberate change.
    """
    w = Warehouse(name="w")
    assert w.delete_on_zero is False


def test_default_preserves_zero_entry_after_remove():
    """Status-quo behavior: remove-to-zero leaves {sku: 0} in stock."""
    w = Warehouse(name="w", stock={"A": 3})
    assert w.remove("A", 3) is True
    assert w.stock == {"A": 0}
    assert "A" in w.stock


# --- Downstream effects under the opt-in flag -----------------------------


def test_stock_alert_under_flag_does_not_see_deleted_sku():
    """Documents the key downstream effect called out in the #21 RFC:
    a SKU removed-to-zero under the flag is invisible to stock_alert,
    including stock_alert(threshold=0). Not asserting this is "good"
    — just pinning the observable behavior for reviewers.
    """
    from inventory.reports import stock_alert
    w = Warehouse(name="w", stock={"A": 3}, delete_on_zero=True)
    w.remove("A", 3)
    assert stock_alert(w, threshold=0) == []


def test_monthly_report_under_flag_omits_deleted_sku():
    """Companion to the above: monthly_report also no longer reports
    the SKU. Compare with the existing #14 regression tests in
    test_reports.py, which assert the opposite under the default.
    """
    from inventory.reports import monthly_report
    w = Warehouse(name="w", stock={"A": 3}, delete_on_zero=True)
    w.remove("A", 3)
    assert monthly_report([w]) == {}
