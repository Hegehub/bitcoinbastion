"""scoring factors and explanations

Revision ID: 20260527_0030
Revises: 20260527_0029
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0030"
down_revision = "20260527_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scoring_factors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("score_id", sa.Integer(), sa.ForeignKey("news_scores.id"), nullable=False),
        sa.Column("factor", sa.String(length=80), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="0"),
        sa.Column("explanation", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_scoring_factors_score_id", "scoring_factors", ["score_id"])
    op.create_index("ix_scoring_factors_factor", "scoring_factors", ["factor"])

    op.create_table(
        "score_explanations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("score_id", sa.Integer(), sa.ForeignKey("news_scores.id"), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("key_factors_json", sa.JSON(), nullable=False),
        sa.Column("limitations_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_score_explanations_score_id", "score_explanations", ["score_id"])


def downgrade() -> None:
    op.drop_index("ix_score_explanations_score_id", table_name="score_explanations")
    op.drop_table("score_explanations")
    op.drop_index("ix_scoring_factors_factor", table_name="scoring_factors")
    op.drop_index("ix_scoring_factors_score_id", table_name="scoring_factors")
    op.drop_table("scoring_factors")
