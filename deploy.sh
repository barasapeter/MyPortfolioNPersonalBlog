#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/ubuntu/MyPortfolioNPersonalBlog"
SERVICE_NAME="fastapi"

echo "==> Pull latest code"
sudo -u ubuntu bash -lc "
  set -e
  cd '$APP_DIR'
  git fetch --all
  git reset --hard origin/main
"

echo "==> Install dependencies"
sudo -u ubuntu bash -lc "
  set -e
  cd '$APP_DIR'
  source venv/bin/activate
  pip install -U pip
  pip install -r requirements.txt
"

echo "==> Restart services"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl reload nginx

echo "✅ Deploy complete: $(date)"
