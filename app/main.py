from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import register_exception_handlers
from app.database import get_db
from app.routers import (
    analytics, audit, auth, fulfillment, inventory, notifications, orders,
    products, returns, shipments, users, warehouses,
)
from app.schemas.common import HealthResponse

app = FastAPI(
    title="Walmart OMS",
    version="1.1.0",
    description="Warehouse Order Management System",
)
register_exception_handlers(app)

for router in (
    auth.router, users.router, products.router, inventory.router, warehouses.router,
    orders.router, fulfillment.router, shipments.router, returns.router,
    notifications.router, audit.router, analytics.router,
):
    app.include_router(router, prefix="/api/v1")


@app.get("/health/live", tags=["System"], response_model=HealthResponse)
def liveness():
    return {"status": "healthy", "service": "walmart-oms", "database": "not_checked"}


@app.get("/health/ready", tags=["System"], response_model=HealthResponse)
def readiness(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ready", "service": "walmart-oms", "database": "healthy"}


@app.get("/health", tags=["System"], response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "service": "walmart-oms", "database": "healthy"}
