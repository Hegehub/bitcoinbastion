from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolLimitations(BaseModel):
    limitations: list[str] = Field(default_factory=list)


class ToolError(BaseModel):
    message: str
    error_code: str = "tool_error"
    limitations: list[str] = Field(default_factory=list)
    safety_flags: dict[str, bool] = Field(default_factory=dict)
    source: str = "bitcoin_bastion_mcp"
    degraded: bool | None = True


class ToolResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    data: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    safety_flags: dict[str, bool] = Field(default_factory=dict)
    source: str = "bitcoin_bastion_mcp"
    degraded: bool | None = None


class SignalToolRequest(BaseModel):
    limit: int = 10
    signal_type: str | None = None


class SignalToolResponse(ToolResponse):
    pass


class TraceAddressRequest(BaseModel):
    address: str


class TraceToolResponse(ToolResponse):
    pass


class TraceReportRequest(BaseModel):
    report_id: int | str


class TraceReportResponse(ToolResponse):
    pass


class WalletHealthRequest(BaseModel):
    wallet_id: str | None = None


class WalletHealthResponse(ToolResponse):
    pass


class PolicyEvaluationRequest(BaseModel):
    policy_profile: str = "default"
    action_type: str = "trace_review"
    context: dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResponse(ToolResponse):
    pass


class TreasuryDraftRequest(BaseModel):
    destination: str
    amount_sats: int
    purpose: str | None = None
    policy_profile: str = "default"


class TreasuryDraftResponse(ToolResponse):
    pass


class ProviderHealthRequest(BaseModel):
    provider_type: str | None = None


class ProviderHealthResponse(ToolResponse):
    pass


class MarketDashboardRequest(BaseModel):
    timeframe: str = "1h"


class MarketDashboardResponse(ToolResponse):
    pass


class EvidencePacketRequest(BaseModel):
    packet_id: int | str


class EvidencePacketResponse(ToolResponse):
    pass
