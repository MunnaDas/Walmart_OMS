from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_user(suffix: str, role: str = "CUSTOMER") -> tuple[int, str]:
    email = f"{role.lower()}-{suffix}@example.com"
    response = client.post("/api/v1/users", json={"name": f"{role} {suffix}", "email": email, "password": "password123", "role": role})
    assert response.status_code == 201, response.text
    user_id = response.json()["id"]
    login = client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})
    assert login.status_code == 200, login.text
    return user_id, login.json()["access_token"]


def setup_admin() -> str:
    _, token = create_user("admin", "ADMIN")
    return token


def test_order_reservation_and_idempotency():
    admin_token = setup_admin()
    customer_id, customer_token = create_user("flow")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    product = client.post("/api/v1/products", headers=admin_headers, json={"sku": "FLOW-001", "name": "Flow Product", "price": 25.0})
    assert product.status_code == 201
    product_id = product.json()["id"]
    warehouse = client.post("/api/v1/warehouses", headers=admin_headers, json={"code": "WH-FLOW", "name": "Flow Warehouse", "capacity": 1000})
    assert warehouse.status_code == 201
    warehouse_id = warehouse.json()["id"]
    assert client.post(f"/api/v1/warehouses/{warehouse_id}/stock", headers=admin_headers, json={"product_id": product_id, "quantity": 10, "bin_code": "A-01"}).status_code == 201
    order = client.post("/api/v1/orders", headers={**customer_headers, "Idempotency-Key": "flow-test-001"}, json={"customer_id": customer_id, "items": [{"product_id": product_id, "quantity": 3}]})
    assert order.status_code == 201
    order_id = order.json()["id"]
    assert order.json()["status"] == "ALLOCATED"
    assert float(order.json()["total_amount"]) == 75.0
    duplicate = client.post("/api/v1/orders", headers={**customer_headers, "Idempotency-Key": "flow-test-001"}, json={"customer_id": customer_id, "items": [{"product_id": product_id, "quantity": 3}]})
    assert duplicate.status_code == 201
    assert duplicate.json()["id"] == order_id
    conflict = client.post("/api/v1/orders", headers={**customer_headers, "Idempotency-Key": "flow-test-001"}, json={"customer_id": customer_id, "items": [{"product_id": product_id, "quantity": 4}]})
    assert conflict.status_code == 409


def test_oversell_is_rejected():
    admin_token = setup_admin()
    first_customer, first_token = create_user("oversell-a")
    second_customer, second_token = create_user("oversell-b")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    product = client.post("/api/v1/products", headers=admin_headers, json={"sku": "OVERSELL-001", "name": "Oversell Product", "price": 5.0})
    assert product.status_code == 201
    pid = product.json()["id"]
    warehouse = client.post("/api/v1/warehouses", headers=admin_headers, json={"code": "WH-OVERSELL", "name": "Oversell Warehouse", "capacity": 100})
    assert warehouse.status_code == 201
    wid = warehouse.json()["id"]
    assert client.post(f"/api/v1/warehouses/{wid}/stock", headers=admin_headers, json={"product_id": pid, "quantity": 5}).status_code == 201
    first = client.post("/api/v1/orders", headers={"Authorization": f"Bearer {first_token}"}, json={"customer_id": first_customer, "items": [{"product_id": pid, "quantity": 5}]})
    assert first.status_code == 201
    second = client.post("/api/v1/orders", headers={"Authorization": f"Bearer {second_token}"}, json={"customer_id": second_customer, "items": [{"product_id": pid, "quantity": 1}]})
    assert second.status_code == 409


def test_health_readiness():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
