#!/bin/bash
set -euo pipefail

DEPLOY_HOST=${DEPLOY_HOST:-alpine-vector-minds.de}
KEY_PATH=${KEY_PATH:-$HOME/.ssh/avm-ec2-key.pem}
REMOTE_USER="ec2-user"
REMOTE_DIR="/opt/app"
LOCAL_BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

if [ ! -f "$KEY_PATH" ]; then
  echo "ERROR: SSH key not found at $KEY_PATH"
  echo "Get the key from the team and place it there, or set KEY_PATH."
  exit 1
fi

SSH_OPTS="-o StrictHostKeyChecking=no -i $KEY_PATH"

mkdir -p "$LOCAL_BACKUP_DIR"

echo "==> Creating database backup on $DEPLOY_HOST..."
ssh $SSH_OPTS "$REMOTE_USER@$DEPLOY_HOST" "
  docker exec avm-db pg_dump -U postgres alpine_vector_minds | gzip
" > "$LOCAL_BACKUP_DIR/avm-db-$TIMESTAMP.sql.gz"

BACKUP_FILE="$LOCAL_BACKUP_DIR/avm-db-$TIMESTAMP.sql.gz"
echo "==> Backup saved to $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Clean up old local backups (keep last 7)
ls -t "$LOCAL_BACKUP_DIR"/avm-db-*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm -f

echo "==> Done."
