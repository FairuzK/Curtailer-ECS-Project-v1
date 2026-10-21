output "app_url" {
  description = "Where the app is reachable."
  value       = local.enable_https ? "https://${var.domain_name}" : "http://${module.alb.alb_dns_name}"
}

output "alb_dns_name" {
  value = module.alb.alb_dns_name
}

output "ecr_repository_url" {
  value = module.ecr.repository_url
}

output "ecr_repository_name" {
  value = module.ecr.repository_name
}

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}

output "ecs_service_name" {
  value = module.ecs.service_name
}

output "aws_region" {
  value = var.aws_region
}

output "github_actions_role_arn" {
  description = "Put this in the GitHub repo variable AWS_ROLE_ARN."
  value       = var.github_repo != "" ? module.github_oidc[0].role_arn : null
}
