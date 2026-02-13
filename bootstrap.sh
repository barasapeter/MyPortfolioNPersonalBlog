#!/usr/bin/env bash
set -euo pipefail

# ========= EDIT THESE =========
DOMAIN="cardlabs.cloud"
EMAIL="barasapeter52@gmail.com"
REPO="https://github.com/barasapeter/MyPortfolioNPersonalBlog.git"
APP_DIR="/home/ubuntu/MyPortfolioNPersonalBlog"
DB_NAME="portfolio_blog"

# Provide password at runtime:
# sudo POSTGRES_PASSWORD='...' ./bootstrap.sh
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
# ==============================

if [[ -z "${POSTGRES_PASSWORD}" ]]; then
  echo "ERROR: POSTGRES_PASSWORD is empty."
  echo "Run like: sudo POSTGRES_PASSWORD='SuperStrongPassword' ./bootstrap.sh"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

echo "==> System update"
apt-get update -y
apt-get upgrade -y

echo "==> Install packages"
apt-get install -y \
  git nginx certbot python3-certbot-nginx \
  python3.12-venv build-essential python3-dev libpq-dev \
  postgresql postgresql-contrib \
  libgl1 libglib2.0-0 libsm6 libxrender1 libxext6

echo "==> Clone/update repo"
if [[ -d "$APP_DIR/.git" ]]; then
  sudo -u ubuntu git -C "$APP_DIR" pull
else
  sudo -u ubuntu git clone "$REPO" "$APP_DIR"
fi

echo "==> venv + requirements"
sudo -u ubuntu bash -lc "
  cd '$APP_DIR'
  python3 -m venv venv
  source venv/bin/activate
  pip install -U pip
  pip install -r requirements.txt
"

echo "==> Write .env"
sudo -u ubuntu bash -lc "cat > '$APP_DIR/.env' <<EOF
POSTGRES_DB=$DB_NAME
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
EOF"

echo "==> Postgres: create db + set password (idempotent)"
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

echo "==> systemd service"
tee /etc/systemd/system/fastapi.service > /dev/null <<EOF
[Unit]
Description=FastAPI app (gunicorn)
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

systemctl daemon-reload
systemctl enable --now fastapi

echo "==> nginx config"
tee /etc/nginx/sites-available/fastapi > /dev/null <<EOF
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

ln -sf /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/fastapi
nginx -t
systemctl restart nginx

echo "==> HTTPS (requires DNS already pointing to this instance)"
certbot --nginx \
  -d "$DOMAIN" -d "www.$DOMAIN" \
  --non-interactive --agree-tos -m "$EMAIL" --redirect || true

echo "==> certbot timer"
systemctl status certbot.timer --no-pager || true

echo "✅ Done."
echo "Check:"
echo "  systemctl status fastapi --no-pager"
echo "  curl -I http://$DOMAIN"
echo "  curl -I https://$DOMAIN"
