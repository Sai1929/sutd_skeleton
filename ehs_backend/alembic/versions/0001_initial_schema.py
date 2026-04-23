"""Initial schema — all tables + pgvector HNSW + BM25 FTS indexes

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ── users ─────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_id", sa.String(50), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="student"),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_users_student_id", "users", ["student_id"])

    # ── activities ────────────────────────────────────────────────
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # ── label_vocab ───────────────────────────────────────────────
    op.create_table(
        "label_vocab",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("step", sa.String(30), nullable=False),
        sa.Column("label_value", sa.String(255), nullable=False),
        sa.Column("label_index", sa.Integer, nullable=False),
        sa.UniqueConstraint("step", "label_value", name="uq_step_label"),
    )
    op.create_index("ix_label_vocab_step", "label_vocab", ["step"])

    # ── inspection_sessions ───────────────────────────────────────
    op.create_table(
        "inspection_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("activity_id", sa.Integer, sa.ForeignKey("activities.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="in_progress"),
        sa.Column("redis_key", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # ── recommendation_steps ──────────────────────────────────────
    op.create_table(
        "recommendation_steps",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inspection_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.SmallInteger, nullable=False),
        sa.Column("step_name", sa.String(30), nullable=False),
        sa.Column("model_input_text", sa.Text, nullable=False),
        sa.Column("ranked_options", postgresql.JSONB, nullable=False),
        sa.Column("selected_label", sa.String(255), nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("session_id", "step_number", name="uq_session_step"),
    )

    # ── inspection_submissions ────────────────────────────────────
    op.create_table(
        "inspection_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inspection_sessions.id"), unique=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("activity_name", sa.String(100), nullable=False),
        sa.Column("hazard_type", sa.String(255), nullable=True),
        sa.Column("severity_likelihood", sa.String(255), nullable=True),
        sa.Column("moc_ppe", sa.String(255), nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_submissions_activity", "inspection_submissions", ["activity_name"])
    op.create_index("ix_submissions_date", "inspection_submissions", ["submitted_at"])
    op.create_index("ix_submissions_user", "inspection_submissions", ["user_id"])

    # ── quizzes ───────────────────────────────────────────────────
    op.create_table(
        "quizzes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("inspection_sessions.id"), unique=True, nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("prompt_used", sa.Text, nullable=True),
        sa.Column("total_questions", sa.SmallInteger, nullable=False, server_default="5"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
    )

    # ── quiz_questions ────────────────────────────────────────────
    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_number", sa.SmallInteger, nullable=False),
        sa.Column("question_type", sa.String(20), nullable=False),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("options", postgresql.JSONB, nullable=True),
        sa.Column("correct_answer", sa.Text, nullable=False),
        sa.Column("explanation", sa.Text, nullable=True),
    )

    # ── quiz_attempts ─────────────────────────────────────────────
    op.create_table(
        "quiz_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("feedback", sa.Text, nullable=True),
    )

    # ── quiz_answers ──────────────────────────────────────────────
    op.create_table(
        "quiz_answers",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.BigInteger, sa.ForeignKey("quiz_questions.id"), nullable=False),
        sa.Column("student_answer", sa.Text, nullable=False),
        sa.Column("is_correct", sa.Boolean, nullable=True),
        sa.Column("partial_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("llm_feedback", sa.Text, nullable=True),
    )

    # ── document_chunks (pgvector) ────────────────────────────────
    op.execute("""
        CREATE TABLE document_chunks (
            id           BIGSERIAL PRIMARY KEY,
            source_type  VARCHAR(30) NOT NULL,
            source_id    UUID NOT NULL,
            chunk_index  INTEGER NOT NULL,
            chunk_text   TEXT NOT NULL,
            token_count  INTEGER,
            activity_name VARCHAR(100),
            hazard_type  VARCHAR(255),
            submitted_at TIMESTAMPTZ,
            user_id      UUID,
            embedding    vector(1536),
            ts_vector    TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # HNSW index (cosine distance, m=12, ef_construction=200)
    op.execute("""
        CREATE INDEX idx_chunks_hnsw ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 12, ef_construction = 200)
    """)

    # GIN index for BM25 full-text search
    op.execute("CREATE INDEX idx_chunks_fts ON document_chunks USING GIN (ts_vector)")

    # Metadata indexes for self-query filter push-down
    op.execute("CREATE INDEX idx_chunks_activity ON document_chunks (activity_name)")
    op.execute("CREATE INDEX idx_chunks_date ON document_chunks (submitted_at)")
    op.execute("CREATE INDEX idx_chunks_source ON document_chunks (source_type, source_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS document_chunks CASCADE")
    op.drop_table("quiz_answers")
    op.drop_table("quiz_attempts")
    op.drop_table("quiz_questions")
    op.drop_table("quizzes")
    op.drop_table("inspection_submissions")
    op.drop_table("recommendation_steps")
    op.drop_table("inspection_sessions")
    op.drop_table("label_vocab")
    op.drop_table("activities")
    op.drop_table("users")
