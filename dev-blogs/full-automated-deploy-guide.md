Cool, we can mirror those console clicks almost 1:1 in Terraform. Below is a Terraform setup that matches your manual provisioning requirements exactly:

* **Name tag:** `portfolio-prod-machine`
* **AMI:** **Ubuntu Server 24.04 LTS** (HVM, SSD)
* **Instance type:** `t3.micro`
* **No key pair** (so `key_name` is not set)
* **Security group:** SSH from `0.0.0.0/0`, HTTP/HTTPS from internet
* **Root volume:** `8 GiB`, **gp3**, **3000 IOPS**, **not encrypted**
* (Optional) **Attach your existing Elastic IP** `52.6.232.178`
* Runs your deploy script using **user_data** on first boot

---

## 1) Folder layout

```
iac-fastapi/
  main.tf
  variables.tf
  outputs.tf
  bootstrap.sh   # your script exactly
```

Put your script in `bootstrap.sh` (same content you posted).

---

## 2) `variables.tf`

```hcl
variable "region" {
  type    = string
  default = "us-east-1"
}

variable "instance_name" {
  type    = string
  default = "portfolio-prod-machine"
}

# Optional: set this if you want to attach your existing Elastic IP
variable "eip_public_ip" {
  type    = string
  default = "52.6.232.178"
}

# If you don't want EIP association, set this to false at apply time
variable "attach_eip" {
  type    = bool
  default = true
}

# Used by your bootstrap script (it requires it)
# ⚠️ Note: this will end up in terraform state if passed directly.
variable "postgres_password" {
  type      = string
  sensitive = true
}
```

---

## 3) `main.tf`

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# --- Ubuntu 24.04 LTS (Noble) AMI from Canonical ---
data "aws_ami" "ubuntu_2404" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# --- Default VPC / default subnet (simple console-like provisioning) ---
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

locals {
  subnet_id = data.aws_subnets.default.ids[0]

  user_data = <<-EOF
    #!/bin/bash
    set -euo pipefail

    # Drop bootstrap script onto instance
    cat > /home/ubuntu/bootstrap.sh <<'SCRIPT'
    ${file("${path.module}/bootstrap.sh")}
    SCRIPT

    chmod +x /home/ubuntu/bootstrap.sh
    chown ubuntu:ubuntu /home/ubuntu/bootstrap.sh

    # Run bootstrap (your script requires POSTGRES_PASSWORD)
    export POSTGRES_PASSWORD='${var.postgres_password}'
    sudo -E /home/ubuntu/bootstrap.sh

    echo "bootstrap completed" > /home/ubuntu/BOOTSTRAP_DONE
  EOF
}

# --- Security Group (matches your manual rules) ---
resource "aws_security_group" "portfolio_sg" {
  name        = "${var.instance_name}-sg"
  description = "portfolio-prod-machine SG"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH from anywhere (as requested)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.instance_name}-sg"
  }
}

# --- EC2 instance (NO key pair) ---
resource "aws_instance" "portfolio" {
  ami           = data.aws_ami.ubuntu_2404.id
  instance_type = "t3.micro"
  subnet_id     = local.subnet_id

  vpc_security_group_ids = [aws_security_group.portfolio_sg.id]

  # NO key pair (matches your manual requirement)
  # key_name = ...

  user_data = local.user_data

  # Root volume: 8GiB gp3, 3000 IOPS, not encrypted
  root_block_device {
    volume_type = "gp3"
    volume_size = 8
    iops        = 3000
    encrypted   = false
  }

  tags = {
    Name = var.instance_name
  }
}

# --- Existing Elastic IP association (optional) ---
data "aws_eip" "existing" {
  count     = var.attach_eip ? 1 : 0
  public_ip = var.eip_public_ip
}

resource "aws_eip_association" "attach" {
  count         = var.attach_eip ? 1 : 0
  instance_id   = aws_instance.portfolio.id
  allocation_id = data.aws_eip.existing[0].id
}
```

---

## 4) `outputs.tf`

```hcl
output "instance_id" {
  value = aws_instance.portfolio.id
}

output "public_ip" {
  value = var.attach_eip ? var.eip_public_ip : aws_instance.portfolio.public_ip
}

output "name" {
  value = aws_instance.portfolio.tags["Name"]
}
```

---

## 5) Deploy

```bash
terraform init

terraform apply -var="postgres_password=SuperStrongPassword"
```

If you *don’t* want to associate the EIP (for testing):

```bash
terraform apply -var="postgres_password=SuperStrongPassword" -var="attach_eip=false"
```

---

## Important reality check (because you said “no key pair”)

* **No key pair** means you **cannot SSH in**, even though port 22 is open.
* Your app can still deploy via **user_data**, but if something fails you’ll want logs.

Two easy ways to see logs without SSH:

1. **EC2 console System Log** (quick sanity check)
2. Add **SSM Session Manager** (best practice). If you want, I’ll drop in the Terraform bits to attach the SSM role so you can shell into it without keys.

---

If you want, paste your current Terraform directory (or tell me which region your EIP is in) and I’ll adjust this so the subnet selection is deterministic (e.g., pick a specific AZ), and I can add an option to **wait for cloud-init completion** and print a “deployment status” via instance logs.
