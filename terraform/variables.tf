variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Used as a name prefix for all resources."
  type        = string
  default     = "url-shortener"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "cpu" {
  description = "Fargate task CPU units (256 = 0.25 vCPU)."
  type        = number
  default     = 256
}

variable "memory" {
  description = "Fargate task memory in MiB."
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "MUST stay 1 while using SQLite: each task has its own private database."
  type        = number
  default     = 1
}

variable "initial_image_tag" {
  description = "Tag used for the very first task definition. CI deploys immutable git-SHA tags afterwards."
  type        = string
  default     = "latest"
}

# ---- Optional HTTPS (leave both empty to run HTTP-only on the ALB DNS name) ----
variable "domain_name" {
  description = "Full app hostname, e.g. short.example.com. Empty = HTTP only."
  type        = string
  default     = ""
}

variable "hosted_zone_name" {
  description = "Existing Route53 public hosted zone, e.g. example.com. Required if domain_name is set."
  type        = string
  default     = ""
}

# ---- GitHub Actions OIDC ----
variable "github_repo" {
  description = "GitHub repo allowed to deploy, as OWNER/REPO. Empty = skip creating the CI role."
  type        = string
  default     = ""
}

variable "create_oidc_provider" {
  description = "Set false if this AWS account already has the GitHub OIDC provider (only one per account)."
  type        = bool
  default     = true
}
