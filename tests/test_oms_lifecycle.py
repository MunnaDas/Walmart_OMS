from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_customer(suffix: str) -> int:
    response = client.post(
        "/api/v1/users",
        json={
            "name": f"Customer {suffix}",
            "email": f"customer-{suffix}@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_order_reservation_and_idempotency():
    customer_id = create_customer("flow")
    product = client.post(
        "/api/v1/products",
        json={"sku": "FLOW-001", "name": "Flow Product", "price": 25.0},
    )
    assert product.status_code == 201
    product_id = product.json()["id"]

    warehouse = client.post(
        "/api/v1/warehouses",
        json={"code": "WH-FLOW", "name": "Flow Warehouse", "capacity": 1000},
    )
    assert warehouse.status_code == 201
    warehouse_id = warehouse.json()["id"]

    stock = client.post(
        f"/api/v1/warehouses/{warehouse_id}/stock",
        json={"product_id": product_id, "quantity": 10, "bin_code": "A-01"},
    )
    assert stock.status_code == 201

    order = client.post(
        "/api/v1/orders",
        headers={"Idempotency-Key": "flow-test-001"},
        json={"customer_id": customer_id, "items": [{"product_id": product_id, "quantity": 3}]},
    )
    assert order.status_code == 201
    order_id = order.json()["id"]
    assert order.json()["status"] == "ALLOCATED"
    assert order.json()["total_amount"] == "75.00"

    duplicate = client.post(
        "/api/v1/orders",
        headers={"Idempotency-Key": "flow-test-001"},
        json={"customer_id": customer_id, "items": [{"product_id": product_id, "quantity": 3}]},
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["id"] == order_id

    conflict = client.post(
        "/api/v1/orders",
        headers={"Idempotency-Key": "flow-test-001"},
        json={"customer_id": customer_id, "items": [{"product_id": product_id, "quantity": 4}]},
    )
    assert conflict.status_code == 409


def test_oversell_is_rejected():
    first_customer = create_customer("oversell-a")
    second_customer = create_customer("oversell-b")
    product = client.post(
        "/api/v1/products",
        json={"sku": "OVERSELL-001", "name": "Oversell Product", "price": 5.0},
    )
    assert product.status_code == 201
    pid = product.json()["id"]
    warehouse = client.post(
        "/api/v1/warehouses",
        json={"code": "WH-OVERSELL", "name": "Oversell Warehouse", "capacity": 100},
    )
    assert warehouse.status_code == 201
    wid = warehouse.json()["id"]
    assert client.post(
        f"/api/v1/warehouses/{wid}/stock", json={"product_id": pid, "quantity": 5}
    ).status_code == 201

    first = client.post(
        "/api/v1/orders",
        json={"customer_id": first_customer, "items": [{"product_id": pid, "quantity": 5}]},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/orders",
        json={"customer_id": second_customer, "items": [{"product_id": pid, "quantity": 1}]},
    )
    assert second.status_code == 409
