"""production observability runtime health

Revision ID: 20260527_0049
Revises: 20260527_0048
Create Date: 2026-06-05 00:49:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260527_0049"
down_revision = "20260527_0048"
branch_labels = None
depends_on = None

json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "system_health_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("system_state", sa.String(length=24), nullable=False, server_default="healthy"),
        sa.Column("summary", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("degraded_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("critical_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fallback_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "operator_attention_required", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("snapshot_json", json_type, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_system_health_snapshots_system_state", "system_health_snapshots", ["system_state"]
    )
    op.create_index(
        "ix_system_health_snapshots_created_at", "system_health_snapshots", ["created_at"]
    )

    op.create_table(
        "provider_health_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_name", sa.String(length=120), nullable=False),
        sa.Column("provider_type", sa.String(length=64), nullable=False),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_latency_ms", sa.Float(), nullable=True),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="1"),
        sa.Column("backoff_until", sa.DateTime(), nullable=True),
        sa.Column("health_state", sa.String(length=24), nullable=False, server_default="healthy"),
        sa.Column("details_json", json_type, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_provider_health_snapshots_provider_name", "provider_health_snapshots", ["provider_name"]
    )
    op.create_index(
        "ix_provider_health_snapshots_provider_type", "provider_health_snapshots", ["provider_type"]
    )
    op.create_index(
        "ix_provider_health_snapshots_health_state", "provider_health_snapshots", ["health_state"]
    )
    op.create_index(
        "ix_provider_health_snapshots_created_at", "provider_health_snapshots", ["created_at"]
    )

    op.create_table(
        "background_job_health",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_name", sa.String(length=160), nullable=False),
        sa.Column("last_start_at", sa.DateTime(), nullable=True),
        sa.Column("last_finish_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("failure_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("worker_name", sa.String(length=120), nullable=False, server_default="unknown"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_background_job_health_job_name", "background_job_health", ["job_name"])
    op.create_index("ix_background_job_health_success", "background_job_health", ["success"])
    op.create_index("ix_background_job_health_created_at", "background_job_health", ["created_at"])

    op.create_table(
        "service_health_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("service_name", sa.String(length=120), nullable=False),
        sa.Column("health_state", sa.String(length=24), nullable=False, server_default="healthy"),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("details_json", json_type, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_service_health_snapshots_service_name", "service_health_snapshots", ["service_name"]
    )
    op.create_index(
        "ix_service_health_snapshots_health_state", "service_health_snapshots", ["health_state"]
    )
    op.create_index(
        "ix_service_health_snapshots_created_at", "service_health_snapshots", ["created_at"]
    )

    op.create_table(
        "runtime_state_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("system_state", sa.String(length=24), nullable=False, server_default="healthy"),
        sa.Column("provider_state", sa.String(length=24), nullable=False, server_default="healthy"),
        sa.Column("job_state", sa.String(length=24), nullable=False, server_default="healthy"),
        sa.Column(
            "signal_pipeline_state", sa.String(length=24), nullable=False, server_default="healthy"
        ),
        sa.Column(
            "evidence_pipeline_state",
            sa.String(length=24),
            nullable=False,
            server_default="healthy",
        ),
        sa.Column("telegram_state", sa.String(length=24), nullable=False, server_default="healthy"),
        sa.Column("state_json", json_type, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_runtime_state_snapshots_system_state", "runtime_state_snapshots", ["system_state"]
    )
    op.create_index(
        "ix_runtime_state_snapshots_created_at", "runtime_state_snapshots", ["created_at"]
    )

    op.create_table(
        "degraded_component_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("severity", sa.String(length=24), nullable=False),
        sa.Column("affected_component", sa.String(length=160), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("recommendation", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "automatic_fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "operator_attention_required", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("details_json", json_type, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_degraded_component_snapshots_severity", "degraded_component_snapshots", ["severity"]
    )
    op.create_index(
        "ix_degraded_component_snapshots_affected_component",
        "degraded_component_snapshots",
        ["affected_component"],
    )
    op.create_index(
        "ix_degraded_component_snapshots_created_at", "degraded_component_snapshots", ["created_at"]
    )

    op.create_table(
        "recovery_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("component", sa.String(length=160), nullable=False),
        sa.Column("failure_time", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("fallback_activated_at", sa.DateTime(), nullable=True),
        sa.Column("recovery_time", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("automatic", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("operator_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "status", sa.String(length=40), nullable=False, server_default="failure_detected"
        ),
        sa.Column("details_json", json_type, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_recovery_events_component", "recovery_events", ["component"])
    op.create_index("ix_recovery_events_status", "recovery_events", ["status"])
    op.create_index("ix_recovery_events_created_at", "recovery_events", ["created_at"])


def downgrade() -> None:
    for table, indexes in [
        (
            "recovery_events",
            [
                "ix_recovery_events_created_at",
                "ix_recovery_events_status",
                "ix_recovery_events_component",
            ],
        ),
        (
            "degraded_component_snapshots",
            [
                "ix_degraded_component_snapshots_created_at",
                "ix_degraded_component_snapshots_affected_component",
                "ix_degraded_component_snapshots_severity",
            ],
        ),
        (
            "runtime_state_snapshots",
            ["ix_runtime_state_snapshots_created_at", "ix_runtime_state_snapshots_system_state"],
        ),
        (
            "service_health_snapshots",
            [
                "ix_service_health_snapshots_created_at",
                "ix_service_health_snapshots_health_state",
                "ix_service_health_snapshots_service_name",
            ],
        ),
        (
            "background_job_health",
            [
                "ix_background_job_health_created_at",
                "ix_background_job_health_success",
                "ix_background_job_health_job_name",
            ],
        ),
        (
            "provider_health_snapshots",
            [
                "ix_provider_health_snapshots_created_at",
                "ix_provider_health_snapshots_health_state",
                "ix_provider_health_snapshots_provider_type",
                "ix_provider_health_snapshots_provider_name",
            ],
        ),
        (
            "system_health_snapshots",
            ["ix_system_health_snapshots_created_at", "ix_system_health_snapshots_system_state"],
        ),
    ]:
        for index in indexes:
            op.drop_index(index, table_name=table)
        op.drop_table(table)
