"""Add ra_json column to activity_recommendations

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("activity_recommendations", sa.Column("ra_json", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("activity_recommendations", "ra_json")
