"""
db_setup.py — One-time PostgreSQL setup script using SQLAlchemy.

Creates:
  - ehs_user  (with password)
  - ehs_db    (owned by ehs_user)
  - Extensions: vector, pg_trgm, uuid-ossp

Usage:
    python db_setup.py

Edit POSTGRES_PASSWORD below to match your postgres superuser password.
"""

from sqlalchemy import create_engine, text

# ── EDIT THIS ────────────────────────────────────────────────────
POSTGRES_PASSWORD = "Syner123"   # your postgres superuser password
EHS_USER_PASSWORD = "Syner123"   # password you want for ehs_user
# ─────────────────────────────────────────────────────────────────

POSTGRES_URL = f"postgresql+psycopg2://postgres:{POSTGRES_PASSWORD}@localhost:5432/postgres"
EHS_DB_URL   = f"postgresql+psycopg2://postgres:{POSTGRES_PASSWORD}@localhost:5432/ehs_db"


def setup():
    print("Connecting to PostgreSQL as postgres...")

    # AUTOCOMMIT required for CREATE USER / CREATE DATABASE
    engine = create_engine(POSTGRES_URL, isolation_level="AUTOCOMMIT")

    with engine.connect() as conn:

        # Create user (skip if already exists)
        exists = conn.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = 'ehs_user'")
        ).fetchone()

        if exists:
            print("  ehs_user already exists — resetting password")
            conn.execute(text(f"ALTER USER ehs_user WITH PASSWORD '{EHS_USER_PASSWORD}'"))
        else:
            conn.execute(text(f"CREATE USER ehs_user WITH PASSWORD '{EHS_USER_PASSWORD}'"))
            print("  Created user: ehs_user")

        # Create database (skip if already exists)
        db_exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'ehs_db'")
        ).fetchone()

        if db_exists:
            print("  ehs_db already exists — skipping creation")
        else:
            conn.execute(text("CREATE DATABASE ehs_db OWNER ehs_user"))
            print("  Created database: ehs_db")

        conn.execute(text("GRANT ALL PRIVILEGES ON DATABASE ehs_db TO ehs_user"))
        print("  Granted privileges to ehs_user")

    engine.dispose()

    # Connect to ehs_db and enable extensions + grant schema privileges
    # (PostgreSQL 15+ removed auto-grant on public schema — must be explicit)
    print("\nEnabling extensions and granting schema privileges in ehs_db...")
    engine2 = create_engine(EHS_DB_URL, isolation_level="AUTOCOMMIT")

    with engine2.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("  vector  — OK")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        print("  pg_trgm — OK")
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        print("  uuid-ossp — OK")

        # Grant ehs_user full access to create tables in public schema
        conn.execute(text("GRANT ALL ON SCHEMA public TO ehs_user"))
        conn.execute(text("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ehs_user"))
        conn.execute(text("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ehs_user"))
        print("  schema public — permissions granted to ehs_user")

    engine2.dispose()

    print("\nSetup complete!")
    print("Next step: cd ehs_backend && alembic upgrade head")


if __name__ == "__main__":
    setup()
