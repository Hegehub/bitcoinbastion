from app.schemas.bastion_trace import SiemDeliveryStatus, SiemEvent


def mark_placeholder_delivery(event: SiemEvent) -> SiemEvent:
    event.delivery_status = SiemDeliveryStatus.PLACEHOLDER_NOT_DELIVERED
    event.delivered = False
    return event
