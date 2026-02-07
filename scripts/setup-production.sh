#!/bin/bash
set -euo pipefail

# ─── Configuration ──────────────────────────────────────────
DOMAIN="alpine-vector-minds.de"
TF_DIR="infrastructure/terraform/environments/dev"
REMOTE_USER="ec2-user"
REMOTE_DIR="/opt/app"
ENV_FILE=".env.production"

ADMIN_EMAIL="${ADMIN_EMAIL:?Set ADMIN_EMAIL}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-$(openssl rand -base64 16)}"

echo "============================================"
echo "  Alpine Vector Minds — Production Setup"
echo "============================================"
echo ""

# ─── Step 1: Generate .env.production if missing ────────────
if [ ! -f "$ENV_FILE" ]; then
  echo "==> Generating $ENV_FILE with random secrets..."
  GENERATED_SECRET=$(openssl rand -hex 32)
  GENERATED_DB_PASS=$(openssl rand -base64 24 | tr -d '/+=')

  sed \
    -e "s|CHANGE_ME_STRONG_PASSWORD|${GENERATED_DB_PASS}|" \
    -e "s|CHANGE_ME_GENERATE_WITH_openssl_rand_hex_32|${GENERATED_SECRET}|" \
    .env.production.example > "$ENV_FILE"

  echo "    Created $ENV_FILE (review and set OPENAI_API_KEY if needed)"
else
  echo "==> Using existing $ENV_FILE"
fi

# ─── Step 2: Terraform init + apply ─────────────────────────
echo ""
echo "==> Running Terraform to provision infrastructure..."
cd "$TF_DIR"

terraform init -input=false

terraform apply -auto-approve

# Extract outputs (resolve key path to absolute before cd-ing back)
EC2_IP=$(terraform output -raw ec2_public_ip)
KEY_PATH="$(pwd)/$(terraform output -raw private_key_path)"

cd - > /dev/null

# Copy key to conventional location so all team scripts work
SHARED_KEY="$HOME/.ssh/avm-ec2-key.pem"
cp "$KEY_PATH" "$SHARED_KEY"
chmod 600 "$SHARED_KEY"

echo "    EC2 IP: $EC2_IP"
echo "    SSH Key: $KEY_PATH (also copied to $SHARED_KEY)"

# ─── Step 3: Wait for EC2 user-data to complete ────────────
echo ""
echo "==> Waiting for EC2 instance to be ready..."
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -i $KEY_PATH"

for i in $(seq 1 60); do
  if ssh $SSH_OPTS "$REMOTE_USER@$EC2_IP" "test -f /opt/app/setup-complete.txt" 2>/dev/null; then
    echo "    Instance ready after ~$((i * 10))s"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "ERROR: Instance not ready after 10 minutes. Check AWS console."
    exit 1
  fi
  echo "    Waiting... (attempt $i/60)"
  sleep 10
done

# ─── Step 4: Deploy code + .env to server ──────────────────
echo ""
echo "==> Syncing project files to server..."
rsync -avz --delete \
  -e "ssh $SSH_OPTS" \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude '.next' \
  --exclude '__pycache__' \
  --exclude '.venv' \
  --exclude '*.pem' \
  --exclude '.env' \
  --exclude '.env.production' \
  --exclude 'certbot' \
  --exclude 'backups' \
  --exclude '.terraform' \
  --exclude '*.tfstate*' \
  ./ "$REMOTE_USER@$EC2_IP:$REMOTE_DIR/"

echo "==> Copying production environment file..."
scp $SSH_OPTS "$ENV_FILE" "$REMOTE_USER@$EC2_IP:$REMOTE_DIR/.env"

# ─── Step 5: SSL certificate acquisition ───────────────────
echo ""
echo "==> Setting up SSL certificate..."
ssh $SSH_OPTS "$REMOTE_USER@$EC2_IP" "
  cd $REMOTE_DIR

  # Start Nginx with HTTP-only config for cert acquisition
  cp nginx/conf.d/default.conf.initial nginx/conf.d/_active.conf

  docker run -d --name avm-nginx-init \
    -v \$(pwd)/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
    -v \$(pwd)/nginx/conf.d/_active.conf:/etc/nginx/conf.d/default.conf:ro \
    -v \$(pwd)/certbot/www:/var/www/certbot:ro \
    -p 80:80 \
    nginx:alpine

  sleep 3

  # Request certificate
  docker run --rm \
    -v \$(pwd)/certbot/conf:/etc/letsencrypt \
    -v \$(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot certonly \
      --webroot \
      --webroot-path=/var/www/certbot \
      --email $ADMIN_EMAIL \
      --agree-tos \
      --no-eff-email \
      -d $DOMAIN \
      -d www.$DOMAIN

  # Stop temporary Nginx
  docker stop avm-nginx-init && docker rm avm-nginx-init
  rm -f nginx/conf.d/_active.conf
"

# ─── Step 6: Start full production stack ────────────────────
echo ""
echo "==> Starting production stack with HTTPS..."
ssh $SSH_OPTS "$REMOTE_USER@$EC2_IP" "
  cd $REMOTE_DIR
  docker-compose -f docker-compose.prod.yml up -d --build
"

# ─── Step 7: Wait for services and create admin ────────────
echo ""
echo "==> Waiting for API to be healthy..."
for i in $(seq 1 30); do
  if ssh $SSH_OPTS "$REMOTE_USER@$EC2_IP" "docker exec avm-api curl -sf http://localhost:8000/health" 2>/dev/null; then
    echo "    API is healthy."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "WARNING: API health check timed out. Continuing anyway..."
    break
  fi
  sleep 5
done

echo "==> Creating admin user..."
ssh $SSH_OPTS "$REMOTE_USER@$EC2_IP" "
  cd $REMOTE_DIR
  docker exec avm-api uv run python -m api.cli \
    --email '$ADMIN_EMAIL' \
    --password '$ADMIN_PASSWORD'
"

# ─── Step 8: Seed database ────────────────────────────────
echo ""
echo "==> Seeding database (import data, generate embeddings, create indexes)..."

echo "    Importing data..."
ssh $SSH_OPTS "$REMOTE_USER@$EC2_IP" \
  "cd $REMOTE_DIR && docker exec avm-api uv run python -m scripts.import_data"

echo "    Generating embeddings..."
ssh $SSH_OPTS "$REMOTE_USER@$EC2_IP" \
  "cd $REMOTE_DIR && docker exec avm-api uv run python -m scripts.generate_embeddings"

echo "    Creating vector indexes..."
ssh $SSH_OPTS "$REMOTE_USER@$EC2_IP" \
  "cd $REMOTE_DIR && docker exec avm-api uv run python -m scripts.create_vector_indexes"

echo "    Database seeding complete."

# ─── Done ──────────────────────────────────────────────────
echo ""
echo "============================================"
echo "  Production setup complete!"
echo "============================================"
echo ""
echo "  URL:    https://$DOMAIN"
echo "  Admin:  $ADMIN_EMAIL"
echo "  Pass:   $ADMIN_PASSWORD"
echo "  SSH:    ssh -i $KEY_PATH $REMOTE_USER@$EC2_IP"
echo ""
echo "  Save these credentials securely!"
echo "============================================"
