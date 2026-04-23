#!/usr/bin/env bash
# EHS Backend — VM Setup Script (Ubuntu 22.04 / 24.04)
set -euo pipefail

echo "==> [1/7] System packages"
sudo apt-get update -qq
sudo apt-get install -y \
    python3.11 python3.11-venv python3.11-dev \
    build-essential libpq-dev \
    postgresql postgresql-contrib \
    redis-server \
    curl git

echo "==> [2/7] PostgreSQL pgvector extension"
# Install pgvector from source (adjust PG version if needed)
PG_VERSION=$(pg_config --version | grep -oP '\d+' | head -1)
sudo apt-get install -y "postgresql-server-dev-${PG_VERSION}" || true
if ! sudo -u postgres psql -c "SELECT * FROM pg_extension WHERE extname='vector';" | grep -q vector; then
    cd /tmp
    git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git
    cd pgvector
    make && sudo make install
    cd -
fi

echo "==> [3/7] PostgreSQL database + user"
sudo -u postgres psql <<'SQL'
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ehs_user') THEN
        CREATE USER ehs_user WITH PASSWORD 'change_me_in_production';
    END IF;
END
$$;
CREATE DATABASE ehs_db OWNER ehs_user;
\c ehs_db
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
SQL

echo "==> [4/7] Redis configuration"
# Increase maxmemory and set eviction policy
sudo sed -i 's/^# maxmemory .*/maxmemory 512mb/' /etc/redis/redis.conf
sudo sed -i 's/^# maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
sudo systemctl enable --now redis-server
sudo systemctl restart redis-server

echo "==> [5/7] Python virtual environment"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3.11 -m venv "${PROJECT_DIR}/.venv"
source "${PROJECT_DIR}/.venv/bin/activate"
pip install --upgrade pip setuptools wheel
pip install -e "${PROJECT_DIR}[all]"
python -m spacy download en_core_web_sm

echo "==> [6/7] Database migrations"
cd "${PROJECT_DIR}"
alembic upgrade head

echo "==> [7/7] Systemd service (optional)"
# Creates a systemd unit that auto-starts the API on boot
SERVICE_FILE="/etc/systemd/system/ehs-backend.service"
sudo tee "${SERVICE_FILE}" > /dev/null <<EOF
[Unit]
Description=EHS Inspection Backend API
After=network.target postgresql.service redis-server.service

[Service]
Type=exec
User=${USER}
WorkingDirectory=${PROJECT_DIR}
EnvironmentFile=${PROJECT_DIR}/.env
ExecStart=${PROJECT_DIR}/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ehs-backend

echo ""
echo "✓ Setup complete."
echo "  Edit .env with your Azure OpenAI credentials, then:"
echo "  sudo systemctl start ehs-backend"
echo "  curl http://localhost:8000/health/ready"
