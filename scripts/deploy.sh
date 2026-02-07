#!/bin/bash
set -euo pipefail

# ─── Configuration ──────────────────────────────────────────
TF_DIR="infrastructure/terraform/environments/dev"
REMOTE_USER="ec2-user"
REMOTE_DIR="/opt/app"
ENV_FILE=".env.production"

# Get host and key from env vars, falling back to terraform state
EC2_IP=${EC2_IP:-$(cd "$TF_DIR" && terraform output -raw ec2_public_ip)}
KEY_PATH=${KEY_PATH:-"$TF_DIR/$(cd "$TF_DIR" && terraform output -raw private_key_path)"}
SSH_OPTS="-o StrictHostKeyChecking=no -i $KEY_PATH"

echo "==> Deploying to $EC2_IP..."

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
  ./ "$REMOTE_USER@$EC2_IP:$REMOTE_DIR/"

# Copy production env
if [ -f "$ENV_FILE" ]; then
  echo "==> Syncing $ENV_FILE..."
  scp $SSH_OPTS "$ENV_FILE" "$REMOTE_USER@$EC2_IP:$REMOTE_DIR/.env"
fi

# Rebuild and restart
echo "==> Building and restarting containers..."
ssh $SSH_OPTS "$REMOTE_USER@$EC2_IP" "
  cd $REMOTE_DIR
  docker-compose -f docker-compose.prod.yml up -d --build
  docker-compose -f docker-compose.prod.yml ps
"

echo "==> Deployment complete!"
