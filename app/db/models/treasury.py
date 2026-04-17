from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class TreasuryRequest(Base):
    __tablename__ = "treasury_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_reference: Mapped[str] = mapped_column(String(120), default="")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    amount_sats: Mapped[int] = mapped_column(Integer, default=0)
    destination_reference: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(40), default="pending")
    priority: Mapped[str] = mapped_column(String(30), default="normal")
    requested_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approved_by_json: Mapped[str] = mapped_column(Text, default="[]")
    required_approvals: Mapped[int] = mapped_column(Integer, default=1)
    policy_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class PsbtWorkflow(Base):
    __tablename__ = "psbt_workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    treasury_request_id: Mapped[int] = mapped_column(ForeignKey("treasury_requests.id"), index=True)
    psbt_reference: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(40), default="draft")
    signer_requirements_json: Mapped[str] = mapped_column(Text, default="{}")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class TreasuryPolicy(Base):
    __tablename__ = "treasury_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    min_wallet_health_score: Mapped[int] = mapped_column(Integer, default=60)
    max_single_tx_sats: Mapped[int] = mapped_column(Integer, default=10_000_000)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("treasury_policies.id"), index=True)
    rule_key: Mapped[str] = mapped_column(String(120), index=True)
    rule_value: Mapped[str] = mapped_column(String(255), default="")
    severity: Mapped[str] = mapped_column(String(30), default="warning")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class PolicyExecutionLog(Base):
    __tablename__ = "policy_execution_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_name: Mapped[str] = mapped_column(String(120), index=True)
    wallet_health_score: Mapped[int] = mapped_column(Integer)
    transaction_amount_sats: Mapped[int] = mapped_column(Integer)
    allowed: Mapped[bool] = mapped_column(default=False)
    violations_json: Mapped[str] = mapped_column(Text, default="[]")
    next_actions_json: Mapped[str] = mapped_column(Text, default="[]")
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
