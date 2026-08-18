from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.enums import FULFILLMENT_TRANSITIONS, FulfillmentStatus
from app.models import Fulfillment, Order, Package


class FulfillmentService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, fulfillment_id: int) -> Fulfillment | None:
        return self.db.get(Fulfillment, fulfillment_id)

    def advance(self, fulfillment: Fulfillment, target: str) -> None:
        current = FulfillmentStatus(fulfillment.status)
        expected = FULFILLMENT_TRANSITIONS.get(current)
        if expected != target:
            raise ValueError(f"Cannot transition {current} -> {target}")
        fulfillment.status = target

    def start_picking(self, fulfillment: Fulfillment, picker_id: str) -> None:
        self.advance(fulfillment, FulfillmentStatus.PICKING)
        fulfillment.picker_id = picker_id
        self.db.get(Order, fulfillment.order_id).status = FulfillmentStatus.PICKING

    def complete_picking(self, fulfillment: Fulfillment) -> None:
        self.advance(fulfillment, FulfillmentStatus.PICKED)
        self.db.get(Order, fulfillment.order_id).status = FulfillmentStatus.PICKED

    def start_packing(self, fulfillment: Fulfillment) -> None:
        self.advance(fulfillment, FulfillmentStatus.PACKING)
        self.db.get(Order, fulfillment.order_id).status = FulfillmentStatus.PACKING

    def pack(self, fulfillment: Fulfillment, weight: Decimal, dimensions: str) -> Package:
        self.advance(fulfillment, FulfillmentStatus.PACKED)
        order = self.db.get(Order, fulfillment.order_id)
        package = Package(order_id=order.id, weight=weight, dimensions=dimensions, status="PACKED")
        self.db.add(package)
        fulfillment.packed_at = datetime.utcnow()
        order.status = FulfillmentStatus.PACKED
        return package
