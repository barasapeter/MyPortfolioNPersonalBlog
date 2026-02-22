# MyPortfolioNPersonalBlog

A FastAPI-based portfolio and personal blog project with an emphasis on:

- **Request routing** (API + server-rendered pages)
- **Application containerization** (Docker / Docker Compose)
- **Infrastructure provisioning** (Terraform on AWS)

This repository is intentionally both an application codebase and a DevOps playground.

## Tech Stack

- **Backend:** FastAPI, Uvicorn, Gunicorn
- **Templating:** Jinja2 + Markdown rendering
- **Database:** PostgreSQL + SQLAlchemy ORM
- **Auth:** Cookie-based JWT flow (custom auth helpers)
- **Infra as Code:** Terraform (AWS)
- **Runtime / Packaging:** Docker, Docker Compose, systemd, Nginx

## Project Structure

```text
.
├── api/v1/                # API route handlers (auth, create-user, update-profile)
├── web/                   # Web routes and template rendering
├── db/                    # SQLAlchemy models, sessions, base utilities
├── templates/             # HTML templates
├── static/                # Static assets (mounted at /static)
├── main.py                # FastAPI app composition and middleware
├── docker-compose.yaml    # Local containerized app + Postgres
├── Dockerfile             # App image build
├── main.tf                # Terraform AWS infrastructure
├── variables.tf           # Terraform variables
├── outputs.tf             # Terraform outputs
├── bootstrap.sh           # EC2 bootstrap and host provisioning script
└── deploy.sh              # Update/redeploy helper script
```

## Request Routing Overview

The app composes routers in `main.py` and uses `API_V1_STR` (default `/api/v1`) for API endpoints.

### Router mounting

- `auth_router` → `/api/v1`
- `create_user_router` → `/api/v1`
- `update_user_router` → `/api/v1`
- `home_router` → `/`

### Main routes

#### Web routes

- `GET /` → Render home content from `primary.md`
- `GET /blog` → Render published posts
- `GET /login` → Render login page
- `GET /account` → Render account/profile page

#### API routes

- `POST /api/v1/login` → Login and set auth cookies
- `POST /api/v1/create-user` → Create a user after validation
- `POST /api/v1/update-profile` → Update logged-in user profile (including avatar)

### Middleware and app behavior

- HTTP middleware logs request path, status, and latency to `logs/app.log`
- OpenAPI docs are intentionally disabled (`docs_url=None`, `redoc_url=None`, `openapi_url=None`)
- On startup, the app creates tables and seeds baseline data if missing

## Data Model Summary

Core entities are defined in `db/__init__.py`:

- `User`
- `Category`
- `Tag`
- `Post`
- `Comment`
- many-to-many `post_tags`

This supports a blog domain with authorship, taxonomy, post status lifecycle, and threaded comments.

## Running Locally (without Docker)

### 1) Prerequisites

- Python 3.12+
- PostgreSQL running locally

### 2) Configure environment

Copy `.env.example` or create `.env` with:

```env
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=portfolio_blog

JWT_SECRET_KEY=replace_me
AWS_ACCESS_KEY=placeholder
AWS_SECRET_ACCESS_KEY=placeholder
```

### 3) Install and run

```bash
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open: `http://127.0.0.1:8000`

## Running with Docker Compose

### 1) Configure environment

Ensure `.env` includes:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=portfolio_blog
POSTGRES_SERVER=postgres
```

### 2) Start services

```bash
docker compose up --build
```

Services:

- `postgres` (with healthcheck)
- `fastapi` (depends on healthy postgres)

App will be available on `http://127.0.0.1:8000`.

## Infrastructure Setup with Terraform (AWS)

Terraform files provision a single EC2-based deployment target and supporting resources.

### What is provisioned

- AWS provider in a configurable region (default `us-east-1`)
- Ubuntu 24.04 AMI lookup (Canonical owner)
- Default VPC + subnet discovery
- IAM role/profile for **AWS Systems Manager** access
- Security group allowing inbound `22`, `80`, `443`
- EC2 instance (`t3.micro`) with user data bootstrap
- Optional association with an existing Elastic IP

### Required input

`postgres_password` is required and marked sensitive.

### Usage

```bash
terraform init
terraform plan -var='postgres_password=REPLACE_ME'
terraform apply -var='postgres_password=REPLACE_ME'
```

### Outputs

- `instance_id`
- `public_ip`
- `name`

## Host Bootstrap and Deployment Flow

The EC2 `user_data` writes and executes `bootstrap.sh`, which:

1. Installs required OS packages (Nginx, PostgreSQL, Python tooling, etc.)
2. Clones/updates this repository
3. Creates virtual environment and installs dependencies
4. Writes application `.env`
5. Initializes PostgreSQL database/password
6. Installs a systemd service running Gunicorn + Uvicorn worker
7. Configures Nginx reverse proxy
8. Attempts TLS provisioning with Certbot
9. Installs `app-deploy` helper symlink to `deploy.sh`

For updates, `deploy.sh` pulls latest code, reinstalls dependencies, and restarts services.

## Notes

- This project currently stores user password values directly in `password_hash` in parts of the flow; hardening for production should include robust hashing and full security review.
- API docs are disabled by default.
- Several deployment values (domain/email/repo URL) are currently hardcoded in `bootstrap.sh` and should be parameterized for reuse.
