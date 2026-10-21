variable "name" { type = string }
variable "github_repo" { type = string } # OWNER/REPO

variable "branch" {
  description = "Only workflows running on this branch may assume the role."
  type        = string
  default     = "main"
}

variable "create_oidc_provider" {
  type    = bool
  default = true
}

variable "ecr_repository_arn" { type = string }
variable "ecs_service_arn" { type = string }
variable "pass_role_arns" { type = list(string) }
