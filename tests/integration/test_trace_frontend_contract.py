from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_trace_client_routes_exist_in_backend() -> None:
    trace_client = read("frontend/bastion_ui/services/trace_client.py")
    sdk_trace = read("sdk/python/bitcoin_bastion_sdk/resources/trace.py")
    backend_trace = read("app/api/v1/trace.py")
    backend_public = read("app/api/v1/public.py")
    required = [
        "/lite/{address}",
        "/address/{address}",
        "/report/{report_id}",
        "/report/{report_id}/evidence",
        "/report/{report_id}/privacy-shield",
        "/report/{report_id}/origin-passport",
        "/report/{report_id}/provider-disagreement",
        "/report/{report_id}/counterparty-lens",
        "/report/{report_id}/policy-facts",
        "/trace/{report_id}/summary",
    ]
    combined_clients = trace_client + sdk_trace
    for route in required:
        assert route in combined_clients
        assert route in backend_trace or route in backend_public


def test_trace_public_safety_contract_is_present() -> None:
    safety = read("frontend/bastion_ui/security/safety_copy.py")
    for phrase in [
        "Advisory-only",
        "Not legal verification",
        "Not Bitcoin consensus proof",
        "No custody",
        "Public Bitcoin addresses only",
        "Never enter seed phrases, private keys, wallet files or signing material",
    ]:
        assert phrase in safety
