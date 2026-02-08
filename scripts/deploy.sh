#!/bin/bash
set -euo pipefail

# ─── Configuration ──────────────────────────────────────────
DEPLOY_HOST=${DEPLOY_HOST:-alpine-vector-minds.de}
KEY_PATH=${KEY_PATH:-$HOME/.ssh/avm-ec2-key.pem}
REMOTE_USER="ec2-user"
REMOTE_DIR="/opt/app"
ENV_FILE=".env.production"

if [ ! -f "$KEY_PATH" ]; then
  echo "ERROR: SSH key not found at $KEY_PATH"
  echo "Get the key from the team and place it there, or set KEY_PATH."
  exit 1
fi

SSH_OPTS="-o StrictHostKeyChecking=no -i $KEY_PATH"

echo "==> Deploying to $DEPLOY_HOST..."

# Sync project files
rsync -avz --delete \
  -e "ssh $SSH_OPTS" \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude '.next' \
  --exclude '__pycache__' \
  --exclude '.venv' \
  --exclude '*.pem' \
  --exclude '.env' \
  --exclude '.env.*' \
  --exclude 'certbot' \
  --exclude 'backups' \
  --exclude '.terraform' \
  --exclude '*.tfstate*' \
  --exclude 'submission' \
  ./ "$REMOTE_USER@$DEPLOY_HOST:$REMOTE_DIR/"

# Copy production env
if [ -f "$ENV_FILE" ]; then
  echo "==> Syncing $ENV_FILE..."
  scp $SSH_OPTS "$ENV_FILE" "$REMOTE_USER@$DEPLOY_HOST:$REMOTE_DIR/.env"
fi

# Rebuild and restart
echo "==> Building and restarting containers..."
ssh $SSH_OPTS "$REMOTE_USER@$DEPLOY_HOST" "
  cd $REMOTE_DIR
  docker-compose -f docker-compose.prod.yml up -d --build
  docker-compose -f docker-compose.prod.yml ps
"

echo "==> Deployment complete!"
