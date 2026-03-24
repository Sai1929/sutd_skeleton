"""Remove redis_key; add state_json to inspection_sessions; add conversation_history table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-23 00:00:00
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── inspection_sessions: swap redis_key → state_json ──────────
    op.drop_column("inspection_sessions", "redis_key")
    op.add_column(
        "inspection_sessions",
        sa.Column("state_json", postgresql.JSONB, nullable=True),
    )

    # ── conversation_history table ────────────────────────────────
    op.create_table(
        "conversation_history",
        sa.Column("conv_id", sa.String(255), primary_key=True),
        sa.Column("messages", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_conv_history_updated_at", "conversation_history", ["updated_at"])


def downgrade() -> None:
    op.drop_index("ix_conv_history_updated_at", table_name="conversation_history")
    op.drop_table("conversation_history")
    op.drop_column("inspection_sessions", "state_json")
    op.add_column(
        "inspection_sessions",
        sa.Column("redis_key", sa.String(255), nullable=True),
    )
