"""Token quota tracking — token_budgets + token_usage_log

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-28
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import TIMESTAMPTZ

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Daily token counter per student
    op.create_table(
        "token_budgets",
        sa.Column("student_id", sa.Text, nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("tokens_used", sa.Integer, nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("student_id", "date"),
    )
    op.create_index("ix_token_budgets_student_date", "token_budgets", ["student_id", "date"])

    # Full audit log
    op.create_table(
        "token_usage_log",
        sa.Column("id", sa.BigInteger, autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Text, nullable=False),
        sa.Column("endpoint", sa.Text, nullable=False),
        sa.Column("tokens_in", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", TIMESTAMPTZ, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_token_usage_log_student", "token_usage_log", ["student_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_token_usage_log_student", "token_usage_log")
    op.drop_table("token_usage_log")
    op.drop_index("ix_token_budgets_student_date", "token_budgets")
    op.drop_table("token_budgets")
