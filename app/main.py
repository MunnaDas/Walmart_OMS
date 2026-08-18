from fastapi import FastAPI

from app.routers import (
    analytics,
    audit,
    fulfillment,
    inventory,
    notifications,
    orders,
    products,
    returns,
    shipments,
    users,
    warehouses,
)

app = FastAPI(
    title="Walmart OMS",
    version="1.0.0",
    description="Warehouse Order Management System",
)

for router in (
    users.router,
    products.router,
    inventory.router,
    warehouses.router,
    orders.router,
    fulfillment.router,
    shipments.router,
    returns.router,
    notifications.router,
    audit.router,
    analytics.router,
):
    app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["System"])
def health():
    return {"status": "healthy", "service": "walmart-oms"}
