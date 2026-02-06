#!/bin/bash
set -euo pipefail

# Update system
dnf update -y

# Install Docker and tools
dnf install -y docker git rsync
systemctl enable docker
systemctl start docker

# Install Docker Compose
DOCKER_COMPOSE_VERSION="v2.32.4"
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Add ec2-user to docker group
usermod -aG docker ec2-user

# Create app directory
mkdir -p /opt/app
chown ec2-user:ec2-user /opt/app

# Create SSL directory structure
mkdir -p /opt/app/certbot/conf
mkdir -p /opt/app/certbot/www

echo "User data setup complete" > /opt/app/setup-complete.txt
