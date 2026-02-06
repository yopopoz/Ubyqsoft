#!/bin/bash

# Script de déploiement pour la mise à jour Logistique API
echo "🚀 Starting Logistics API Update Deployment..."

# 1. Pull latest code
echo "📥 Pulling latest git changes..."
git pull origin main

# 2. Rebuild/Restart Backend & Frontend
# We need to restart to make sure new python code is loaded and frontend is rebuilt with new pages.
# Check for docker compose or docker compose
# Check for docker compose
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    echo "⚠️ Docker compose not found, trying 'docker compose' anyway..."
    COMPOSE_CMD="docker compose"
fi

echo "🔄 Rebuilding and restarting containers (using $COMPOSE_CMD)..."
$COMPOSE_CMD -f docker-compose.prod.yml up -d --build backend frontend

# Wait a few seconds for DB connection to be ready if it was restarting
echo "⏳ Waiting 5s for service stabilization..."
sleep 5

# 3. Run Database Migration
# This runs the safe column addition script inside the running container
echo "🗄️ Running Database Migration..."
docker exec -it logistics_backend_prod python /app/add_logistics_columns.py

echo "✅ Logistics Update Deployed Successfully!"
echo "   - Code updated"
echo "   - Backend restarted"
echo "   - Database columns added (api_logs, carrier_scac, etc.)"
