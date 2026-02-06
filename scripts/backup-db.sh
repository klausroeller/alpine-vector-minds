#!/bin/bash
set -euo pipefail

TF_DIR="infrastructure/terraform/environments/dev"
REMOTE_USER="ec2-user"
REMOTE_DIR="/opt/app"
LOCAL_BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Get host and key from terraform state
EC2_IP=$(cd "$TF_DIR" && terraform output -raw ec2_public_ip)
KEY_PATH="$TF_DIR/$(cd "$TF_DIR" && terraform output -raw private_key_path)"
SSH_OPTS="-o StrictHostKeyChecking=no -i $KEY_PATH"

mkdir -p "$LOCAL_BACKUP_DIR"

echo "==> Creating database backup on $EC2_IP..."
ssh $SSH_OPTS "$REMOTE_USER@$EC2_IP" "
  docker exec avm-db pg_dump -U postgres alpine_vector_minds | gzip
" > "$LOCAL_BACKUP_DIR/avm-db-$TIMESTAMP.sql.gz"

BACKUP_FILE="$LOCAL_BACKUP_DIR/avm-db-$TIMESTAMP.sql.gz"
echo "==> Backup saved to $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Clean up old local backups (keep last 7)
ls -t "$LOCAL_BACKUP_DIR"/avm-db-*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm -f

echo "==> Done."
