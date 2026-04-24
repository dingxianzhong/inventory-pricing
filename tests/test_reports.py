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
