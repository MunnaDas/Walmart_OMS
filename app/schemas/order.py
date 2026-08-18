from decimal import Decimal
from pydantic import BaseModel, Field
from app.schemas.common import ORMModel


class OrderItemResponse(ORMModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: Decimal


class OrderResponse(ORMModel):
    id: int
    customer_id: int
    status: str
    total_amount: Decimal
    idempotency_key: str | None = None


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    limit: int
    offset: int
    count: int
