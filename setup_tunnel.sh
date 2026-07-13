#!/bin/bash
# setup_tunnel.sh - Zero-Cost Cloudflare Tunnel Configuration for Project Junglee

echo "================================================="
echo "   JARVIS ZERO-COST CLOUDFLARE TUNNEL SETUP      "
echo "================================================="

# 1. Download and install cloudflared
echo "[1] Installing cloudflared daemon..."
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
rm cloudflared-linux-amd64.deb

# 2. Authenticate with Cloudflare
echo "[2] Authenticating with Cloudflare..."
echo "Please click the link that appears below to log into your Cloudflare account and authorize the tunnel."
cloudflared tunnel login

# 3. Create Tunnel
echo "[3] Creating the Jarvis Secure Tunnel..."
cloudflared tunnel create jarvis-tunnel
TUNNEL_ID=$(cloudflared tunnel list | grep jarvis-tunnel | awk '{print $1}')

# 4. Configure Ingress Rules
echo "[4] Configuring Ingress Rules for the FastAPI Command Center..."
mkdir -p ~/.cloudflared
cat <<EOF > ~/.cloudflared/config.yml
tunnel: $TUNNEL_ID
credentials-file: /home/$USER/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: junglee001.*
    service: http://localhost:8001
  - service: http_status:404
EOF

# 5. Route DNS
echo "[5] Routing DNS..."
echo "Please enter your free domain (e.g., yourdomain.tk, yourdomain.ml) that is managed by Cloudflare:"
read DOMAIN

# Update config.yml with actual domain
sed -i "s/junglee001.*/junglee001.$DOMAIN/g" ~/.cloudflared/config.yml

# Map the CNAME record automatically
cloudflared tunnel route dns jarvis-tunnel "junglee001.$DOMAIN"

# 6. Run the tunnel in the background
echo "[6] Starting the tunnel..."
# Note: For full production, run `sudo cloudflared service install`
cloudflared tunnel run jarvis-tunnel &

echo "================================================="
echo "   TUNNEL ONLINE!                                "
echo "   Access Dashboard: http://junglee001.$DOMAIN/api/v1/dashboard/?api_key=jarvis_junglee"
echo "================================================="
