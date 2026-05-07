#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Nirnay — One-Shot GCP Backend Deploy Script
# Paste this ENTIRE block into your SSH terminal and hit Enter.
# ─────────────────────────────────────────────────────────────────────────────
set -e   # exit on any error

# ── 1. Collect inputs up-front ───────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║         Nirnay Backend — GCP Deploy Setup           ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

read -rp "GitHub repo URL (e.g. https://github.com/you/nirnay): " REPO_URL
read -rp "DuckDNS subdomain  (e.g. nirnay-api  → nirnay-api.duckdns.org): " DUCK_SUBDOMAIN
read -rp "DuckDNS token: " DUCK_TOKEN
read -rp "Groq API key (gsk_...): " GROQ_KEY
read -rp "Firebase Project ID: " FIREBASE_PROJECT

echo ""
echo "► Starting deployment..."
echo ""

# ── 2. System update ─────────────────────────────────────────────────────────
sudo apt-get update -qq && sudo apt-get upgrade -y -qq

# ── 3. Install Docker ────────────────────────────────────────────────────────
echo "► Installing Docker..."
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
fi
sudo apt-get install -y -qq docker-compose-plugin
echo "  Docker $(docker --version)"

# ── 4. Install Caddy ─────────────────────────────────────────────────────────
echo "► Installing Caddy..."
if ! command -v caddy &>/dev/null; then
  sudo apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
    | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
    | sudo tee /etc/apt/sources.list.d/caddy-stable.list > /dev/null
  sudo apt-get update -qq && sudo apt-get install -y -qq caddy
fi
echo "  Caddy $(caddy version)"

# ── 5. Clone repo ────────────────────────────────────────────────────────────
echo "► Cloning repo..."
if [ -d "$HOME/nirnay" ]; then
  echo "  Repo already exists — pulling latest..."
  git -C "$HOME/nirnay" pull
else
  git clone "$REPO_URL" "$HOME/nirnay"
fi

# ── 6. Write backend .env ────────────────────────────────────────────────────
echo "► Writing backend/.env..."
mkdir -p "$HOME/nirnay/backend/data/db" \
         "$HOME/nirnay/backend/data/uploads" \
         "$HOME/nirnay/backend/data/exports"

cat > "$HOME/nirnay/backend/.env" << EOF
GROQ_API_KEY=${GROQ_KEY}
GROQ_DEFAULT_MODEL=llama-3.3-70b-versatile
DATABASE_URL=sqlite:///./data/db/nirnay.db
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./data/uploads
EXPORTS_PATH=./data/exports
FIREBASE_PROJECT_ID=${FIREBASE_PROJECT}
EOF
echo "  Written ✓"

# ── 7. Set up DuckDNS auto-update ────────────────────────────────────────────
echo "► Setting up DuckDNS..."
mkdir -p "$HOME/duckdns"
cat > "$HOME/duckdns/duck.sh" << EOF
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=${DUCK_SUBDOMAIN}&token=${DUCK_TOKEN}&ip=" \
  | curl -sk -o "$HOME/duckdns/duck.log" -K -
EOF
chmod +x "$HOME/duckdns/duck.sh"
"$HOME/duckdns/duck.sh"
DUCK_RESULT=$(cat "$HOME/duckdns/duck.log")
echo "  DuckDNS update result: $DUCK_RESULT"
if [ "$DUCK_RESULT" != "OK" ]; then
  echo "  ⚠ DuckDNS update failed — check your subdomain/token and retry."
fi
# Add to cron (skip if already there)
( crontab -l 2>/dev/null | grep -v duck.sh; echo "*/5 * * * * $HOME/duckdns/duck.sh" ) | crontab -

# ── 8. Configure Caddyfile ───────────────────────────────────────────────────
echo "► Configuring Caddyfile..."
CADDYFILE="$HOME/nirnay/backend/Caddyfile"
# Replace the placeholder subdomain in the Caddyfile from the repo
sed -i "s/YOUR_SUBDOMAIN/${DUCK_SUBDOMAIN}/g" "$CADDYFILE"

sudo cp "$CADDYFILE" /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl enable caddy --quiet
sudo systemctl restart caddy
echo "  Caddy started ✓"

# ── 9. Build & start Docker container ────────────────────────────────────────
echo "► Building and starting Docker container..."
cd "$HOME/nirnay"
# Use newgrp to run docker as the docker group (avoids needing logout)
sg docker -c "docker compose -f docker-compose.prod.yml up -d --build"
echo "  Container started ✓"

# ── 10. Wait for health check ────────────────────────────────────────────────
echo "► Waiting for backend to become healthy..."
for i in $(seq 1 20); do
  sleep 3
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/healthz 2>/dev/null || true)
  if [ "$HTTP" = "200" ]; then
    echo "  Backend healthy ✓ (attempt $i)"
    break
  fi
  echo "  Attempt $i — waiting..."
done

# ── 11. Final summary ────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║                  Deploy Complete!                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  Internal:  curl http://127.0.0.1:8080/healthz"
echo "  External:  https://${DUCK_SUBDOMAIN}.duckdns.org/healthz"
echo ""
echo "  📌 Next: add this to Vercel env vars:"
echo "     VITE_API_BASE_URL=https://${DUCK_SUBDOMAIN}.duckdns.org"
echo ""
echo "  📋 Useful commands:"
echo "     Logs:    docker compose -f ~/nirnay/docker-compose.prod.yml logs -f backend"
echo "     Restart: docker compose -f ~/nirnay/docker-compose.prod.yml restart backend"
echo "     Update:  cd ~/nirnay && git pull && docker compose -f docker-compose.prod.yml up -d --build"
echo ""
