#!/bin/bash
# Cloud9 ERP - DigitalOcean Droplet Deployment Script
# Run this on a fresh Ubuntu 22.04 LTS Droplet
# 
# Usage:
#   chmod +x deploy.droplet.sh
#   ./deploy.droplet.sh
#
# Prerequisites:
#   - SSH access to Droplet
#   - Domain: erp.cloud9beverages.com pointing to Droplet IP
#   - Git configured on Droplet

set -e

echo "=========================================="
echo "Cloud9 ERP - Droplet Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="erp.cloud9beverages.com"
REPO_URL="https://github.com/admiralsuez/c9-erp.git"
APP_DIR="/opt/cloud9-erp"
EMAIL="admin@cloud9beverages.com"

echo -e "${YELLOW}Step 1: System Updates${NC}"
sudo apt-get update
sudo apt-get upgrade -y
echo -e "${GREEN}✓ System updated${NC}\n"

echo -e "${YELLOW}Step 2: Install Docker${NC}"
# Remove old Docker versions if present
sudo apt-get remove -y docker docker.io docker-doc docker-compose podman-docker containerd runc 2>/dev/null || true

# Install Docker using official repository
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo groupadd -f docker
sudo usermod -aG docker $USER

echo -e "${GREEN}✓ Docker installed${NC}\n"

echo -e "${YELLOW}Step 3: Install Nginx${NC}"
sudo apt-get install -y nginx certbot python3-certbot-nginx curl
sudo systemctl enable nginx
echo -e "${GREEN}✓ Nginx installed${NC}\n"

echo -e "${YELLOW}Step 4: Configure Firewall (UFW)${NC}"
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
echo -e "${GREEN}✓ Firewall configured${NC}\n"

echo -e "${YELLOW}Step 5: Clone Repository${NC}"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR
cd $APP_DIR
git clone $REPO_URL .
echo -e "${GREEN}✓ Repository cloned${NC}\n"

echo -e "${YELLOW}Step 6: Setup Environment Variables${NC}"
if [ ! -f ".env" ]; then
    cp .env.production.example .env
    echo -e "${YELLOW}⚠️  WARNING: Please edit .env with your actual values:${NC}"
    echo "   sudo nano .env"
    echo ""
    echo "   Required values:"
    echo "   - DB_PASSWORD: Strong password for PostgreSQL"
    echo "   - JWT_SECRET: Generate with: openssl rand -hex 32"
    echo ""
    read -p "Press Enter after configuring .env..."
else
    echo "   .env already exists, skipping..."
fi
echo -e "${GREEN}✓ Environment configured${NC}\n"

echo -e "${YELLOW}Step 7: Configure Nginx${NC}"
sudo cp nginx.conf /etc/nginx/sites-available/cloud9-erp
sudo ln -sf /etc/nginx/sites-available/cloud9-erp /etc/nginx/sites-enabled/cloud9-erp
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t
echo -e "${GREEN}✓ Nginx configured${NC}\n"

echo -e "${YELLOW}Step 8: Setup SSL Certificate (Let's Encrypt)${NC}"
echo "Waiting 10 seconds for DNS to propagate..."
sleep 10

sudo certbot certonly --standalone \
  --non-interactive \
  --agree-tos \
  --email $EMAIL \
  -d $DOMAIN

echo -e "${GREEN}✓ SSL certificate installed${NC}\n"

echo -e "${YELLOW}Step 9: Start Nginx${NC}"
sudo systemctl restart nginx
echo -e "${GREEN}✓ Nginx started${NC}\n"

echo -e "${YELLOW}Step 10: Start Docker Containers${NC}"
cd $APP_DIR
docker compose -f docker-compose.production.yml up -d

# Wait for containers to start
echo "Waiting for containers to start..."
sleep 15

echo -e "${GREEN}✓ Docker containers started${NC}\n"

echo -e "${YELLOW}Step 11: Verify Deployment${NC}"
echo "Checking container status..."
docker compose -f docker-compose.production.yml ps

echo ""
echo "Checking API health..."
curl -s https://$DOMAIN/api/health || echo "API not responding yet (normal during first startup)"

echo -e "${GREEN}✓ Deployment verification complete${NC}\n"

echo "=========================================="
echo -e "${GREEN}✓ DEPLOYMENT COMPLETE!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Access the application: https://$DOMAIN"
echo "2. Login with: admin@example.com / admin@123"
echo "3. Change admin password immediately"
echo "4. Configure company settings"
echo ""
echo "Useful commands:"
echo "  View logs:        docker compose -f docker-compose.production.yml logs -f"
echo "  Restart services: docker compose -f docker-compose.production.yml restart"
echo "  Stop all:         docker compose -f docker-compose.production.yml down"
echo "  Check status:     docker compose -f docker-compose.production.yml ps"
echo ""
echo "Setup automatic certificate renewal:"
echo "  sudo systemctl enable certbot.timer"
echo "  sudo systemctl start certbot.timer"
echo ""
