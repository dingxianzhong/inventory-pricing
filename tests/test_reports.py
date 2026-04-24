from inventory.models import Warehouse
from inventory.reports import monthly_report, stock_alert


def test_stock_alert_below_threshold():
    w = Warehouse(name="main", stock={"A": 5, "B": 20})
    assert stock_alert(w, threshold=10) == ["A"]


def test_stock_alert_at_threshold_included():
    w = Warehouse(name="main", stock={"A": 10, "B": 20})
    assert stock_alert(w, threshold=10) == ["A"]


def test_stock_alert_boundary_just_below_threshold():
    # qty == threshold - 1 -> reported.
    w = Warehouse(name="main", stock={"A": 9})
    assert stock_alert(w, threshold=10) == ["A"]


def test_stock_alert_boundary_exact_threshold():
    # qty == threshold -> reported (inclusive).
    w = Warehouse(name="main", stock={"A": 10})
    assert stock_alert(w, threshold=10) == ["A"]


def test_stock_alert_boundary_just_above_threshold():
    # qty == threshold + 1 -> NOT reported.
    w = Warehouse(name="main", stock={"A": 11})
    assert stock_alert(w, threshold=10) == []


def test_monthly_report_single_warehouse():
    w = Warehouse(name="main", stock={"A": 5, "B": 3})
    report = monthly_report([w])
    assert report == {"A": 5, "B": 3}


def test_monthly_report_multiple_warehouses():
    w1 = Warehouse(name="main", stock={"A": 5, "B": 3})
    w2 = Warehouse(name="overflow", stock={"A": 2, "C": 7})
    report = monthly_report([w1, w2])
    assert report == {"A": 7, "B": 3, "C": 7}


# --- Zero-quantity SKU preservation (regression for #14) ------------------

def test_monthly_report_single_warehouse_preserves_zero_sku():
    """A SKU with stock 0 in a single warehouse must still appear in the
    aggregate report with value 0 (not dropped).
    """
    w = Warehouse(name="main", stock={"A": 0})
    report = monthly_report([w])
    assert report == {"A": 0}
    assert "A" in report


def test_monthly_report_split_preserves_zero_sku_from_one_side():
    """When one partition has no entry for a SKU and the other has it at
    qty 0, the aggregate across both must still include that SKU at 0.
    This is the split case that exposed a bug in the property-test helper
    (Counter.__add__ drops zero counts); monthly_report itself must keep
    it.
    """
    left = Warehouse(name="left", stock={"B": 5})       # no "A"
    right = Warehouse(name="right", stock={"A": 0})     # "A" at zero
    report = monthly_report([left, right])
    assert report == {"A": 0, "B": 5}
    assert "A" in report


def test_monthly_report_multiple_zero_contributions_sum_to_zero():
    """Two warehouses each contributing 0 for the same SKU should still
    leave that SKU in the aggregate at 0 (not filter it out).
    """
    w1 = Warehouse(name="w1", stock={"A": 0})
    w2 = Warehouse(name="w2", stock={"A": 0})
    report = monthly_report([w1, w2])
    assert report == {"A": 0}
    assert "A" in report


def test_monthly_report_mixed_zero_and_positive_for_same_sku():
    """Zero in one warehouse plus a positive value in another should sum
    normally; zero must not be treated as 'absent'.
    """
    w1 = Warehouse(name="w1", stock={"A": 0, "B": 4})
    w2 = Warehouse(name="w2", stock={"A": 3})
    report = monthly_report([w1, w2])
    assert report == {"A": 3, "B": 4}
