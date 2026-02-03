#!/bin/bash
# Server Setup Script
# Usage: ./scripts/setup_server.sh <server_ip>

SERVER_IP=$1
USER="root"

if [ -z "$SERVER_IP" ]; then
  echo "Usage: $0 <server_ip>"
  exit 1
fi

echo "Connecting to $SERVER_IP to set up prerequisites..."

ssh $USER@$SERVER_IP << 'EOF'
  set -e

  echo "Updating system packages..."
  apt update && apt upgrade -y

  echo "Installing Git and basic tools..."
  apt install -y git curl

  # Install Docker if not verified
  if ! command -v docker &> /dev/null; then
      echo "Installing Docker..."
      curl -fsSL https://get.docker.com -o get-docker.sh
      sh get-docker.sh
      rm get-docker.sh
  else
      echo "Docker is already installed."
  fi

  echo "Verifying Docker Compose..."
  docker compose version

  echo "Creating application directory at /opt/bbox-l..."
  mkdir -p /opt/bbox-l

  echo "Setup complete! You can now use deploy.sh"
EOF
