"""activity_recommendations table

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "activity_recommendations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("activity_input", sa.Text(), nullable=False),
        sa.Column("activity_normalized", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("hazard_types", ARRAY(sa.Text()), nullable=False),
        sa.Column("severity_likelihood", sa.Text(), nullable=False),
        sa.Column("moc_ppe", sa.Text(), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Trigram index for fuzzy text search
    op.execute(
        "CREATE INDEX idx_act_rec_trgm ON activity_recommendations "
        "USING gin (activity_normalized gin_trgm_ops)"
    )

    # HNSW index for vector search
    op.execute(
        "CREATE INDEX idx_act_rec_hnsw ON activity_recommendations "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 12, ef_construction = 200)"
    )


def downgrade() -> None:
    op.drop_table("activity_recommendations")
