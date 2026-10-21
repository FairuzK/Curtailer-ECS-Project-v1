variable "name" { type = string }
variable "vpc_id" { type = string }
variable "subnet_ids" { type = list(string) }
variable "container_port" { type = number }

variable "enable_https" {
  description = "Separate boolean (not derived from certificate_arn) because the ARN is unknown at plan time."
  type        = bool
  default     = false
}

variable "certificate_arn" {
  type    = string
  default = ""
}
