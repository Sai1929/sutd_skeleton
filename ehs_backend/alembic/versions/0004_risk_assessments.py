"""risk_assessments table

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # vector + pg_trgm already enabled by 0003 — no need to re-enable

    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_input", sa.Text(), nullable=False),
        sa.Column("project_input_normalized", sa.Text(), nullable=False),
        sa.Column("project_name", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=True),   # stored as vector via raw SQL below
        sa.Column("ra_markdown", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Replace TEXT placeholder with actual vector column
    op.execute("ALTER TABLE risk_assessments ALTER COLUMN embedding TYPE vector(384) USING NULL::vector(384)")

    # GIN trigram index for fuzzy text search
    op.execute(
        "CREATE INDEX ix_ra_trgm ON risk_assessments "
        "USING GIN (project_input_normalized gin_trgm_ops)"
    )

    # HNSW index for fast cosine vector search
    op.execute(
        "CREATE INDEX ix_ra_embedding_hnsw ON risk_assessments "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m=12, ef_construction=200)"
    )

    op.create_index("ix_ra_project_input_normalized", "risk_assessments", ["project_input_normalized"])


def downgrade() -> None:
    op.drop_table("risk_assessments")
