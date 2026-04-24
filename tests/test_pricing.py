import pytest

from inventory.models import Order, Product
from inventory.pricing import apply_discount, bulk_price, compute_total


def test_apply_discount_10_percent():
    assert apply_discount(100.0, 10.0) == pytest.approx(90.0)


def test_apply_discount_zero():
    assert apply_discount(100.0, 0.0) == pytest.approx(100.0)


def test_apply_discount_full():
    assert apply_discount(100.0, 100.0) == pytest.approx(0.0)


def test_apply_discount_negative_raises():
    with pytest.raises(ValueError):
        apply_discount(100.0, -0.01)
    with pytest.raises(ValueError):
        apply_discount(100.0, -10.0)


def test_apply_discount_above_100_raises():
    with pytest.raises(ValueError):
        apply_discount(100.0, 100.01)
    with pytest.raises(ValueError):
        apply_discount(100.0, 150.0)


def test_apply_discount_nan_raises():
    with pytest.raises(ValueError):
        apply_discount(100.0, float("nan"))


def test_apply_discount_boundaries_accepted():
    # Exact boundaries are valid.
    assert apply_discount(100.0, 0.0) == pytest.approx(100.0)
    assert apply_discount(100.0, 100.0) == pytest.approx(0.0)


def test_compute_total_invalid_discount_raises():
    # compute_total should inherit validation via apply_discount.
    catalog = {"A": Product(sku="A", name="Apple", unit_price=2.0)}
    order = Order(order_id="o1", items=[("A", 3)])
    with pytest.raises(ValueError):
        compute_total(order, catalog, discount_pct=-1.0)
    with pytest.raises(ValueError):
        compute_total(order, catalog, discount_pct=101.0)


def test_compute_total_simple():
    catalog = {"A": Product(sku="A", name="Apple", unit_price=2.0)}
    order = Order(order_id="o1", items=[("A", 3)])
    assert compute_total(order, catalog) == pytest.approx(6.0)


def test_compute_total_with_discount():
    catalog = {"A": Product(sku="A", name="Apple", unit_price=10.0)}
    order = Order(order_id="o1", items=[("A", 2)])
    assert compute_total(order, catalog, discount_pct=25.0) == pytest.approx(15.0)


def test_compute_total_unknown_sku_raises():
    catalog = {"A": Product(sku="A", name="Apple", unit_price=2.0)}
    order = Order(order_id="o1", items=[("B", 1)])
    with pytest.raises(KeyError):
        compute_total(order, catalog)


def test_compute_total_strict_false_skips_unknown_and_warns():
    catalog = {"A": Product(sku="A", name="Apple", unit_price=2.0)}
    order = Order(order_id="o1", items=[("A", 3), ("B", 99)])
    with pytest.warns(DeprecationWarning):
        total = compute_total(order, catalog, strict=False)
    # Only "A" contributes: 3 * 2.0 = 6.0; "B" silently skipped.
    assert total == pytest.approx(6.0)


def test_compute_total_strict_false_with_discount():
    catalog = {"A": Product(sku="A", name="Apple", unit_price=10.0)}
    order = Order(order_id="o1", items=[("A", 2), ("MISSING", 5)])
    with pytest.warns(DeprecationWarning):
        total = compute_total(order, catalog, discount_pct=25.0, strict=False)
    # 2 * 10.0 = 20.0, 25% off -> 15.0.
    assert total == pytest.approx(15.0)


def test_compute_total_strict_false_warning_message_prefix():
    # The prefix is a public contract documented in README.md and
    # CHANGELOG.md so downstreams can filter on it. Do not change it
    # without a major version bump.
    catalog = {"A": Product(sku="A", name="Apple", unit_price=2.0)}
    order = Order(order_id="o1", items=[("A", 1)])
    with pytest.warns(DeprecationWarning) as record:
        compute_total(order, catalog, strict=False)
    assert any(
        str(w.message).startswith(
            "[inventory] compute_total(strict=False) is deprecated"
        )
        for w in record
    )


def test_compute_total_strict_true_does_not_warn():
    catalog = {"A": Product(sku="A", name="Apple", unit_price=2.0)}
    order = Order(order_id="o1", items=[("A", 3)])
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # any warning becomes an exception
        assert compute_total(order, catalog) == pytest.approx(6.0)
        assert compute_total(order, catalog, strict=True) == pytest.approx(6.0)


def test_bulk_price_below_threshold():
    p = Product(sku="A", name="Apple", unit_price=1.0)
    assert bulk_price(p, 50) == pytest.approx(50.0)


def test_bulk_price_at_or_above_threshold_gets_discount():
    p = Product(sku="A", name="Apple", unit_price=1.0)
    assert bulk_price(p, 100) == pytest.approx(90.0)


def test_bulk_price_boundary_99_no_discount():
    p = Product(sku="A", name="Apple", unit_price=1.0)
    # 1 unit below threshold -> full price.
    assert bulk_price(p, 99) == pytest.approx(99.0)


def test_bulk_price_boundary_100_gets_discount():
    p = Product(sku="A", name="Apple", unit_price=1.0)
    # Exactly at threshold -> 10% off.
    assert bulk_price(p, 100) == pytest.approx(90.0)


def test_bulk_price_boundary_101_gets_discount():
    p = Product(sku="A", name="Apple", unit_price=1.0)
    # Above threshold -> 10% off.
    assert bulk_price(p, 101) == pytest.approx(101 * 0.9)
