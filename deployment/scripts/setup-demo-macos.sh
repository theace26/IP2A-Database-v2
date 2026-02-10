#!/bin/bash
# UnionCore Demo — macOS Setup Script
# Adds unioncore.ibew46.local to /etc/hosts and creates .env.demo
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"

echo "╔══════════════════════════════════════════════════════╗"
echo "║        UnionCore Demo Environment Setup              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: /etc/hosts entry ────────────────────────────────
HOSTS_ENTRY="127.0.0.1    unioncore.ibew46.local"

if grep -q "unioncore.ibew46.local" /etc/hosts; then
    echo "✅ /etc/hosts already contains unioncore.ibew46.local"
else
    echo "Adding unioncore.ibew46.local to /etc/hosts (requires sudo)..."
    echo "$HOSTS_ENTRY" | sudo tee -a /etc/hosts > /dev/null
    echo "✅ Added to /etc/hosts"
fi

# ── Step 2: .env.demo file ─────────────────────────────────
ENV_FILE="$DEPLOY_DIR/.env.demo"

if [ -f "$ENV_FILE" ]; then
    echo "✅ .env.demo already exists at $ENV_FILE"
    echo "   Review it to ensure passwords are set."
else
    echo "Creating .env.demo from template..."
    cp "$DEPLOY_DIR/.env.demo.example" "$ENV_FILE"

    # Generate secure defaults
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    DB_PASS="demo_$(python3 -c "import secrets; print(secrets.token_hex(8))")"
    MINIO_PASS="minio_$(python3 -c "import secrets; print(secrets.token_hex(8))")"

    # Replace placeholders (macOS sed syntax)
    sed -i '' "s/CHANGE_ME_generate_a_real_secret/$JWT_SECRET/" "$ENV_FILE"
    sed -i '' "s/CHANGE_ME_demo_password_2026/$DB_PASS/" "$ENV_FILE"
    sed -i '' "s/CHANGE_ME_minio_secret_2026/$MINIO_PASS/" "$ENV_FILE"

    echo "✅ Created .env.demo with generated secrets"
    echo "   Location: $ENV_FILE"
fi

# ── Step 3: Verify Docker ──────────────────────────────────
if docker info > /dev/null 2>&1; then
    echo "✅ Docker Desktop is running"
else
    echo "❌ Docker Desktop is NOT running. Please start it first."
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Setup complete! Next steps:                         ║"
echo "║                                                      ║"
echo "║  cd deployment                                       ║"
echo "║  docker compose -f docker-compose.demo-https.yml \   ║"
echo "║    --env-file .env.demo up -d --build                ║"
echo "║                                                      ║"
echo "║  Then open: https://unioncore.ibew46.local           ║"
echo "╚══════════════════════════════════════════════════════╝"
