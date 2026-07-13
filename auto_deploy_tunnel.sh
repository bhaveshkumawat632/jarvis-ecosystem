#!/bin/bash
# auto_deploy_tunnel.sh - Project Junglee Automated Deployment Protocol

echo "[INIT] Starting Zero-Touch Tunnel Setup..."

if ! command -v cloudflared &> /dev/null; then
    echo "[INSTALL] Installing cloudflared daemon locally..."
    mkdir -p ~/.local/bin
    wget -q -O ~/.local/bin/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
    chmod +x ~/.local/bin/cloudflared
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "[INSTALL] cloudflared is already installed."
fi

# We use stdbuf to ensure the prompt is printed immediately so the agent can read it
if [ ! -f ~/.cloudflared/cert.pem ]; then
    echo "[AUTH] Triggering Cloudflare Authentication..."
    cloudflared tunnel login
else
    echo "[AUTH] Cloudflare certificate already exists."
fi

echo "[INPUT_REQUIRED] Please enter your target domain (e.g., yourdomain.tk):"
read DOMAIN
echo "[ROUTING] Domain received: $DOMAIN"

# Delete any existing tunnel with this name to avoid conflicts
cloudflared tunnel delete -f jarvis-tunnel 2>/dev/null || true

echo "[CONFIG] Creating the Jarvis Secure Tunnel..."
cloudflared tunnel create jarvis-tunnel
TUNNEL_ID=$(cloudflared tunnel list | grep jarvis-tunnel | awk '{print $1}')

echo "[CONFIG] Tunnel ID: $TUNNEL_ID"
echo "[CONFIG] Generating Ingress Rules..."

mkdir -p ~/.cloudflared
cat <<EOF > ~/.cloudflared/config.yml
tunnel: $TUNNEL_ID
credentials-file: /home/$USER/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: junglee001.$DOMAIN
    service: http://localhost:8001
  - service: http_status:404
EOF

echo "[ROUTING] Mapping DNS CNAME record for junglee001.$DOMAIN..."
cloudflared tunnel route dns jarvis-tunnel "junglee001.$DOMAIN"

echo "[TEST] Running internal diagnostic check..."
if grep -q "localhost:8001" ~/.cloudflared/config.yml; then
    echo "[TEST] Port 8001 successfully mapped in ingress rules."
else
    echo "[TEST] ERROR: Port 8001 mapping failed."
fi

echo "[DEPLOY] Starting the tunnel in the background..."
cloudflared tunnel run jarvis-tunnel > ~/.cloudflared/tunnel.log 2>&1 &

echo "[SUCCESS] Auto-Deployment Complete. The tunnel is active."
