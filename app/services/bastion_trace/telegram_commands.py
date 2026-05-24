from app.services.bastion_trace.trace_service import TraceService


def build_check_message(service: TraceService, address: str) -> str:
    data = service.build_lite_report(address)
    return f"Bitcoin Bastion Lite Check\n\nStatus: {data['status_label']}\nRisk: {data['risk_label']}\nWarning: Never enter seed phrases or private keys."
