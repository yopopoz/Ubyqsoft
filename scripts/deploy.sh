#!/bin/bash
# Deployment Script
# Usage: ./scripts/deploy.sh <server_ip> <repo_url>

SERVER_IP=$1
REPO_URL=$2
USER="root"
APP_DIR="/opt/bbox-l"

if [ -z "$SERVER_IP" ] || [ -z "$REPO_URL" ]; then
  echo "Usage: $0 <server_ip> <repo_url>"
  echo "Example: ./scripts/deploy.sh 82.112.253.118 https://github.com/myuser/myrepo.git"
  exit 1
fi

echo "Deploying to $SERVER_IP from $REPO_URL..."

ssh $USER@$SERVER_IP << EOF
  set -e
  
  # Ensure directory exists
  mkdir -p $APP_DIR
  cd $APP_DIR

  # Clone or Pull
  if [ ! -d ".git" ]; then
    echo "Cloning repository for the first time..."
    git clone "$REPO_URL" .
  else
    echo "Pulling latest changes..."
    git pull origin main
  fi

  # Build and Start Containers
  echo "Building and starting containers..."
  docker compose -f docker-compose.prod.yml down
  docker compose -f docker-compose.prod.yml up -d --build

  echo "Pruning unused images..."
  docker image prune -f

  echo "Deployment to production successful!"
EOF
