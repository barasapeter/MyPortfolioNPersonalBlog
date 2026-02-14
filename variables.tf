variable "region" {
  type    = string
  default = "us-east-1"
}

variable "instance_name" {
  type    = string
  default = "managed-prod-machine"
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
