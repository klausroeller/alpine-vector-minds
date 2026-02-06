#!/bin/bash
set -euo pipefail

DOMAIN="alpine-vector-minds.de"
EMAIL="${ADMIN_EMAIL:?Set ADMIN_EMAIL}"
TF_DIR="infrastructure/terraform/environments/dev"
REMOTE_USER="ec2-user"
REMOTE_DIR="/opt/app"

# Get host and key from terraform state
EC2_IP=$(cd "$TF_DIR" && terraform output -raw ec2_public_ip)
KEY_PATH="$TF_DIR/$(cd "$TF_DIR" && terraform output -raw private_key_path)"
SSH_OPTS="-o StrictHostKeyChecking=no -i $KEY_PATH"

echo "==> Setting up SSL on $EC2_IP for $DOMAIN..."

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
      --email $EMAIL \
      --agree-tos \
      --no-eff-email \
      -d $DOMAIN \
      -d www.$DOMAIN

  # Stop temporary Nginx
  docker stop avm-nginx-init && docker rm avm-nginx-init
  rm -f nginx/conf.d/_active.conf
"

echo "==> SSL setup complete for $DOMAIN."
