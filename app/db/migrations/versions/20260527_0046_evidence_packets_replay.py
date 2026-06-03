"""evidence packets and replay production subsystem

Revision ID: 20260527_0046
Revises: 20260527_0045
Create Date: 2026-05-27 00:46:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260527_0046"
down_revision = "20260527_0045"
branch_labels = None
depends_on = None

json_type = postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "evidence_packets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("packet_type", sa.String(length=64), nullable=False),
        sa.Column("source_entity_type", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("impact_id", sa.Integer(), sa.ForeignKey("news_price_impacts.id"), nullable=True),
        sa.Column("attribution_id", sa.Integer(), sa.ForeignKey("candle_attributions.id"), nullable=True),
        sa.Column("signal_id", sa.Integer(), sa.ForeignKey("intelligence_signal_candidates.id"), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("provider_confidence", sa.Float(), nullable=True),
        sa.Column("source_confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for col in ["packet_type", "source_entity_type", "source_entity_id", "article_id", "event_id", "impact_id", "attribution_id", "signal_id", "created_at"]:
        op.create_index(f"ix_evidence_packets_{col}", "evidence_packets", [col])

    op.create_table(
        "evidence_relationships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("parent_entity_type", sa.String(length=64), nullable=False),
        sa.Column("parent_entity_id", sa.Integer(), nullable=False),
        sa.Column("child_entity_type", sa.String(length=64), nullable=False),
        sa.Column("child_entity_id", sa.Integer(), nullable=False),
        sa.Column("relationship_type", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for col in ["parent_entity_type", "parent_entity_id", "child_entity_type", "child_entity_id", "relationship_type", "created_at"]:
        op.create_index(f"ix_evidence_relationships_{col}", "evidence_relationships", [col])

    op.create_table(
        "evidence_artifacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("packet_id", sa.Integer(), sa.ForeignKey("evidence_packets.id"), nullable=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("artifact_type", sa.String(length=80), nullable=False),
        sa.Column("artifact_json", json_type, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for col in ["packet_id", "entity_type", "entity_id", "artifact_type", "created_at"]:
        op.create_index(f"ix_evidence_artifacts_{col}", "evidence_artifacts", [col])

    op.create_table(
        "evidence_integrity_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("hash_algorithm", sa.String(length=32), nullable=False, server_default="sha256"),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    for col in ["entity_type", "entity_id", "content_hash", "created_at"]:
        op.create_index(f"ix_evidence_integrity_snapshots_{col}", "evidence_integrity_snapshots", [col])

    op.create_table(
        "evidence_replay_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("step_name", sa.String(length=120), nullable=False),
        sa.Column("input_hash", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("output_hash", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("metadata_json", json_type, nullable=False, server_default=sa.text("'{}'")),
    )
    for col in ["entity_type", "entity_id", "step_name", "started_at", "success", "error_code"]:
        op.create_index(f"ix_evidence_replay_logs_{col}", "evidence_replay_logs", [col])


def downgrade() -> None:
    for col in ["error_code", "success", "started_at", "step_name", "entity_id", "entity_type"]:
        op.drop_index(f"ix_evidence_replay_logs_{col}", table_name="evidence_replay_logs")
    op.drop_table("evidence_replay_logs")
    for col in ["created_at", "content_hash", "entity_id", "entity_type"]:
        op.drop_index(f"ix_evidence_integrity_snapshots_{col}", table_name="evidence_integrity_snapshots")
    op.drop_table("evidence_integrity_snapshots")
    for col in ["created_at", "artifact_type", "entity_id", "entity_type", "packet_id"]:
        op.drop_index(f"ix_evidence_artifacts_{col}", table_name="evidence_artifacts")
    op.drop_table("evidence_artifacts")
    for col in ["created_at", "relationship_type", "child_entity_id", "child_entity_type", "parent_entity_id", "parent_entity_type"]:
        op.drop_index(f"ix_evidence_relationships_{col}", table_name="evidence_relationships")
    op.drop_table("evidence_relationships")
    for col in ["created_at", "signal_id", "attribution_id", "impact_id", "event_id", "article_id", "source_entity_id", "source_entity_type", "packet_type"]:
        op.drop_index(f"ix_evidence_packets_{col}", table_name="evidence_packets")
    op.drop_table("evidence_packets")
