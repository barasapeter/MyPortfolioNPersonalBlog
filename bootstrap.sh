#!/usr/bin/env bash
set -euo pipefail

# ========= EDIT THESE =========
DOMAIN="cardlabs.cloud"
EMAIL="barasapeter52@gmail.com"
REPO="https://github.com/barasapeter/MyPortfolioNPersonalBlog.git"
APP_DIR="/home/ubuntu/MyPortfolioNPersonalBlog"
DB_NAME="portfolio_blog"

# Choose a strong password (or export POSTGRES_PASSWORD before running)
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-ChangeMe_StrongPassword}"
# ==============================

export DEBIAN_FRONTEND=noninteractive

echo "==> Updating system packages"
sudo apt-get update -y
sudo apt-get upgrade -y

echo "==> Installing system deps"
sudo apt-get install -y \
  git nginx certbot python3-certbot-nginx \
  python3.12-venv build-essential python3-dev libpq-dev \
  postgresql postgresql-contrib \
  libgl1 libglib2.0-0 libsm6 libxrender1 libxext6

echo "==> Cloning repo (or updating if exists)"
if [ -d "$APP_DIR/.git" ]; then
  sudo -u ubuntu git -C "$APP_DIR" pull
else
  sudo -u ubuntu git clone "$REPO" "$APP_DIR"
fi

echo "==> Creating venv + installing requirements"
sudo -u ubuntu bash -lc "
  cd '$APP_DIR'
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
"

echo "==> Writing .env"
sudo -u ubuntu bash -lc "cat > '$APP_DIR/.env' << 'EOF'
# --- your app env here ---
POSTGRES_DB=$DB_NAME
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
EOF"

echo "==> Configuring Postgres (db + password)"
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$DB_NAME') THEN
    CREATE DATABASE $DB_NAME;
  END IF;
END
\$\$;

ALTER USER postgres WITH PASSWORD '$POSTGRES_PASSWORD';
SQL

echo "==> Creating systemd service"
sudo tee /etc/systemd/system/fastapi.service > /dev/null <<EOF
[Unit]
Description=FastAPI app (gunicorn + uvicorn worker)
After=network.target postgresql.service

[Service]
User=ubuntu
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 127.0.0.1:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now fastapi

echo "==> Nginx site config"
sudo tee /etc/nginx/sites-available/fastapi > /dev/null <<EOF
server {
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/fastapi
sudo nginx -t
sudo systemctl restart nginx

echo "==> TLS with certbot (requires DNS already pointing to this instance)"
sudo certbot --nginx \
  -d "$DOMAIN" -d "www.$DOMAIN" \
  --non-interactive --agree-tos -m "$EMAIL" --redirect

echo "==> Certbot auto-renew timer status"
sudo systemctl status certbot.timer --no-pager || true

echo "✅ Done. Check:"
echo "   - sudo systemctl status fastapi --no-pager"
echo "   - curl -I https://$DOMAIN"
