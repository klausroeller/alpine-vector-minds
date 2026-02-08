#!/bin/bash
set -euo pipefail

# ─── Configuration ──────────────────────────────────────────
DEPLOY_HOST=${DEPLOY_HOST:-alpine-vector-minds.de}
KEY_PATH=${KEY_PATH:-$HOME/.ssh/avm-ec2-key.pem}
REMOTE_USER="ec2-user"
REMOTE_DIR="/opt/app"

if [ ! -f "$KEY_PATH" ]; then
  echo "ERROR: SSH key not found at $KEY_PATH"
  echo "Get the key from the team and place it there, or set KEY_PATH."
  exit 1
fi

SSH_OPTS="-o StrictHostKeyChecking=no -i $KEY_PATH"

echo "============================================"
echo "  Seeding production database"
echo "  Host: $DEPLOY_HOST"
echo "============================================"
echo ""

echo "==> Step 1/6: Importing data..."
ssh $SSH_OPTS "$REMOTE_USER@$DEPLOY_HOST" \
  "cd $REMOTE_DIR && docker exec avm-api uv run python -m scripts.import_data"

echo ""
echo "==> Step 2/6: Migrating ticket embeddings column..."
ssh $SSH_OPTS "$REMOTE_USER@$DEPLOY_HOST" \
  "cd $REMOTE_DIR && docker exec avm-api uv run python -m scripts.migrate_ticket_embeddings"

echo ""
echo "==> Step 3/6: Migrating QA columns..."
ssh $SSH_OPTS "$REMOTE_USER@$DEPLOY_HOST" \
  "cd $REMOTE_DIR && docker exec avm-api uv run python -m scripts.migrate_qa_columns"

echo ""
echo "==> Step 4/6: Generating embeddings..."
ssh $SSH_OPTS "$REMOTE_USER@$DEPLOY_HOST" \
  "cd $REMOTE_DIR && docker exec avm-api uv run python -m scripts.generate_embeddings"

echo ""
echo "==> Step 5/6: Creating vector indexes..."
ssh $SSH_OPTS "$REMOTE_USER@$DEPLOY_HOST" \
  "cd $REMOTE_DIR && docker exec avm-api uv run python -m scripts.create_vector_indexes"

echo ""
echo "==> Step 6/6: Creating full-text search indexes..."
ssh $SSH_OPTS "$REMOTE_USER@$DEPLOY_HOST" \
  "cd $REMOTE_DIR && docker exec avm-api uv run python -m scripts.create_fulltext_indexes"

echo ""
echo "==> Database seeding complete!"
