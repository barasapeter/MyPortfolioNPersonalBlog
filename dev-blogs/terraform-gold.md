# From 1,000 Clicks to 2 Commands

## How I Deployed My Blogging App with Terraform

Building the blogging app was one journey.

Deploying it taught me a different kind of engineering.

This post documents how I moved from manual AWS provisioning to Infrastructure as Code (IaC), the trade-offs I considered, the mistakes I made, and how I built a reproducible deployment pipeline.

---

## Phase 1: The Manual Deployment (a thousand clicks)

After finishing the application, my first production deployment looked like this:

- Log into AWS console
- Create EC2 instance
  - Name: `portfolio-prod-machine`
  - Ubuntu Server 24.04 LTS
  - t3.micro
  - No key pair
  - Open ports 22, 80, 443
  - 8GB gp3 (3000 IOPS)
- Launch instance
- SSH into instance
- Install system dependencies
- Clone repo
- Create virtual environment
- Install requirements
- Install PostgreSQL
- Create database
- Set postgres password
- Install missing CV2 system libraries
- Test gunicorn
- Create systemd service
- Install and configure nginx
- Generate SSL with certbot
- Test renewal

It worked.

But it was fragile.

Every step depended on:
- Human memory
- Manual confirmation prompts
- Correct order of execution
- No typos
- No interruptions

If I wanted to deploy again?

I had to repeat everything.

That was the moment I realized:

> If deployment is manual, it's not engineering. It's ritual.

---

## What Was Wrong With Manual Deployment?

1. **Non-reproducible**
   - If I forgot one step, deployment failed.
   - If I changed instance config later, I had no record.

2. **Not scalable**
   - Creating a second environment (staging) would require repeating everything.

3. **Not testable**
   - No version control for infrastructure.
   - No ability to diff infrastructure changes.

4. **Slow iteration**
   - Fix a bug → SSH → patch → restart.
   - No pipeline.

I needed something deterministic.

---

## Phase 2: Discovering Infrastructure as Code

I started learning Terraform with one goal:

> Deploy my entire production stack with a single command.

The idea was simple:

- Describe infrastructure declaratively.
- Let Terraform handle creation.
- Use `user_data` to bootstrap the instance.
- Attach existing Elastic IP.
- Reproduce everything exactly.

Instead of:

```

Click → Click → Click → Pray

```

I wanted:

```

terraform apply

```

---

## Architecture I Chose

For v1 production:

- EC2 (Ubuntu 24.04)
- Nginx (reverse proxy)
- Gunicorn + Uvicorn workers
- PostgreSQL (local instance)
- Let's Encrypt for SSL
- Elastic IP
- systemd for process management

Why this setup?

Because:

- I wanted full control.
- I wanted to understand Linux process management.
- I wanted to debug real-world issues.
- I wanted to know exactly what production is doing.

No PaaS abstractions.
No Docker.
No managed Postgres (yet).

Just raw infrastructure.

---

## Terraform Design Decisions

### 1. Default VPC vs Custom VPC

Choice:
- Build VPC from scratch
- Use default VPC

I chose default VPC for v1 because:
- Simpler.
- Less noise while learning.
- Focused on deployment automation.

### 2. Elastic IP

Instead of letting EC2 assign a random public IP each time, I:

- Allocated an Elastic IP.
- Attached it via Terraform.

This ensures:
- DNS remains stable.
- Destroy/recreate cycles don’t break domain mapping.

### 3. No Key Pair

I intentionally launched without a key pair.

Why?

Because I wanted:
- Immutable deployments.
- Minimal SSH reliance.
- Everything bootstrapped automatically.

Later I added Session Manager support for safer remote debugging.

---

## The Bootstrap Script

I automated everything I previously did manually:

- apt update/upgrade
- Install system packages
- Clone repo
- Create venv
- Install requirements
- Install PostgreSQL
- Create DB
- Set password
- Create `.env`
- Create systemd service
- Configure nginx
- Generate SSL

All inside one `bootstrap.sh`.

The instance booted.
Cloud-init ran.
Everything configured itself.

When it worked, it felt like magic.

When it broke, it was terrifying.

---

## The 502 Bad Gateway Incident

After deployment, I hit the domain.

Instead of my app, I saw:

```

502 Bad Gateway
nginx/1.24.0

```

Time to debug.

### Step 1: Check systemd

```

sudo systemctl status fastapi
sudo journalctl -u fastapi

```

The logs revealed:

```

ValidationError: AWS_ACCESS_KEY field required
AWS_SECRET_ACCESS_KEY field required

```

My app was crashing on boot.

### Root Cause

My `.env` file was incomplete.

Why?

Because in my bootstrap script I wrote:

```

JWT_SECRET_KEY="i am batman"

```

Inside a double-quoted heredoc.

The shell interpreted the quotes and truncated the file.

Result:

```

JWT_SECRET_KEY=i

````

Everything after that line never got written.

One pair of quotes broke the entire deployment.

That was a powerful lesson:

> Infrastructure failures are often microscopic.

---

## How I Fixed It

I rewrote the heredoc to avoid nested quotes:

```bash
JWT_SECRET_KEY=i am batman
AWS_ACCESS_KEY=lolno
AWS_SECRET_ACCESS_KEY=lol
````

No inner quotes.
No interpolation confusion.

Redeployed.

It worked.

---

## From Manual Ritual to Two Commands

Before:

* 30+ manual steps
* Multiple prompts
* Human-dependent sequence

Now:

```
terraform destroy
terraform apply
```

And the entire production environment rebuilds itself.

Database.
Systemd.
Nginx.
SSL.
Everything.

Reproducible.

Version-controlled.

Deterministic.

---

## Testing Mindset Applied to Infrastructure

While building the app, I learned:

* Write testable modules.
* Separate concerns.
* Validate inputs.

I applied the same thinking to deployment:

* Idempotent scripts.
* Explicit environment variables.
* No hidden state.
* Restart policies in systemd.
* Explicit service binding (`127.0.0.1:8000`).
* Reverse proxy isolation.

Infrastructure became another layer of the system architecture.

---

## Key Lessons Learned

1. Infrastructure is code.
2. Bash quoting matters more than ego.
3. systemd logs are gold.
4. 502 errors are almost always upstream failures.
5. Deterministic environments reduce cognitive load.
6. Manual deployment does not scale your learning.

---

## What’s Next: Continuous Deployment

Now that infrastructure is reproducible, the next step is automation.

Planned improvements:

* GitHub Actions:

  * On push to main:

    * SSH or SSM into instance
    * Pull latest changes
    * Restart service
* Or:

  * Rebuild instance entirely from Terraform
* Move secrets to AWS SSM Parameter Store
* Move PostgreSQL to RDS
* Add staging environment
* Add CloudWatch logging

The goal:

> Push code → production updates automatically.

---

## Final Thoughts

Building the app improved my backend skills.

Automating deployment improved my engineering maturity.

Anyone can deploy manually.

But turning infrastructure into code — versioned, reproducible, and debuggable — changes how you think about systems.

This project wasn't just about blogging.

It was about learning how production actually works.

And now, deploying a new environment is not a ritual.

It’s a command.