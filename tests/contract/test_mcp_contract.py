from pathlib import Path


def test_mcp_contract_exposes_safe_tool_names() -> None:
    source = Path("mcp/bastion_mcp/server.py").read_text(encoding="utf-8")
    for tool in ["get_latest_signals", "analyze_address", "get_trace_report", "evaluate_policy", "create_treasury_draft"]:
        assert tool in source
    assert "broadcast_transaction" not in source
    assert "sign_transaction" not in source
