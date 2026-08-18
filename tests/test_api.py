from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_product_creation_requires_admin():
    unauthenticated = client.post(
        "/api/v1/products",
        json={"sku": "TEST-UNAUTH", "name": "Test Product", "price": 10.0},
    )
    assert unauthenticated.status_code == 401
