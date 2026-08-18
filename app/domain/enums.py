from enum import StrEnum


class OrderStatus(StrEnum):
    CREATED = "CREATED"
    ALLOCATED = "ALLOCATED"
    PICKING = "PICKING"
    PICKED = "PICKED"
    PACKING = "PACKING"
    PACKED = "PACKED"
    READY_TO_SHIP = "READY_TO_SHIP"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class FulfillmentStatus(StrEnum):
    ALLOCATED = "ALLOCATED"
    PICKING = "PICKING"
    PICKED = "PICKED"
    PACKING = "PACKING"
    PACKED = "PACKED"
    READY_TO_SHIP = "READY_TO_SHIP"


FULFILLMENT_TRANSITIONS = {
    FulfillmentStatus.ALLOCATED: FulfillmentStatus.PICKING,
    FulfillmentStatus.PICKING: FulfillmentStatus.PICKED,
    FulfillmentStatus.PICKED: FulfillmentStatus.PACKING,
    FulfillmentStatus.PACKING: FulfillmentStatus.PACKED,
    FulfillmentStatus.PACKED: FulfillmentStatus.READY_TO_SHIP,
}
