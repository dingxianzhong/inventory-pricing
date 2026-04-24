import pytest

from inventory.models import Order, Product, Warehouse


def test_product_rejects_negative_price():
    with pytest.raises(ValueError):
        Product(sku="A", name="Apple", unit_price=-1.0)


def test_warehouse_add_new_sku():
    w = Warehouse(name="main")
    w.add("A", 5)
    assert w.available("A") == 5


def test_warehouse_add_existing_sku():
    w = Warehouse(name="main", stock={"A": 3})
    w.add("A", 4)
    assert w.available("A") == 7


def test_warehouse_remove_success():
    w = Warehouse(name="main", stock={"A": 10})
    assert w.remove("A", 3) is True
    assert w.available("A") == 7


def test_warehouse_remove_insufficient():
    w = Warehouse(name="main", stock={"A": 2})
    assert w.remove("A", 5) is False
    assert w.available("A") == 2


def test_order_total_units():
    o = Order(order_id="o1", items=[("A", 2), ("B", 3)])
    assert o.total_units() == 5


def test_order_is_empty_with_no_items():
    o = Order(order_id="o1", items=[])
    assert o.is_empty() is True


def test_order_is_not_empty_with_items():
    o = Order(order_id="o1", items=[("A", 1)])
    assert o.is_empty() is False
