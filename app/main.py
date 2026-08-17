from fastapi import FastAPI
from app.database import Base, engine
from app.routers import products, inventory, warehouses, orders, fulfillment, shipments, returns, analytics

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Walmart OMS", version="1.0.0", description="Warehouse Order Management System")

for router in (products.router, inventory.router, warehouses.router, orders.router, fulfillment.router, shipments.router, returns.router, analytics.router):
    app.include_router(router, prefix="/api/v1")

@app.get("/health", tags=["System"])
def health():
    return {"status": "healthy", "service": "walmart-oms"}
