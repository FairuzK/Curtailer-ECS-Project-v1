locals {
  name         = "${var.project_name}-${var.environment}"
  enable_https = var.domain_name != ""
}

module "network" {
  source = "./modules/network"
  name   = local.name
}

module "ecr" {
  source = "./modules/ecr"
  name   = local.name
}

# ---- HTTPS (optional) ----
data "aws_route53_zone" "this" {
  count        = local.enable_https ? 1 : 0
  name         = var.hosted_zone_name
  private_zone = false
}

module "acm" {
  count       = local.enable_https ? 1 : 0
  source      = "./modules/acm"
  domain_name = var.domain_name
  zone_id     = data.aws_route53_zone.this[0].zone_id
}

module "alb" {
  source          = "./modules/alb"
  name            = local.name
  vpc_id          = module.network.vpc_id
  subnet_ids      = module.network.public_subnet_ids
  container_port  = var.container_port
  enable_https    = local.enable_https
  certificate_arn = local.enable_https ? module.acm[0].certificate_arn : ""
}

resource "aws_route53_record" "app" {
  count   = local.enable_https ? 1 : 0
  zone_id = data.aws_route53_zone.this[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = module.alb.alb_dns_name
    zone_id                = module.alb.alb_zone_id
    evaluate_target_health = true
  }
}

module "ecs" {
  source = "./modules/ecs"

  name                  = local.name
  aws_region            = var.aws_region
  vpc_id                = module.network.vpc_id
  subnet_ids            = module.network.public_subnet_ids
  alb_security_group_id = module.alb.alb_security_group_id
  target_group_arn      = module.alb.target_group_arn
  container_image       = "${module.ecr.repository_url}:${var.initial_image_tag}"
  container_port        = var.container_port
  cpu                   = var.cpu
  memory                = var.memory
  desired_count         = var.desired_count

  # The service can't attach to the target group until a listener exists.
  depends_on = [module.alb]
}

module "github_oidc" {
  count  = var.github_repo != "" ? 1 : 0
  source = "./modules/github_oidc"

  name                 = local.name
  github_repo          = var.github_repo
  create_oidc_provider = var.create_oidc_provider
  ecr_repository_arn   = module.ecr.repository_arn
  ecs_service_arn      = module.ecs.service_arn
  pass_role_arns       = [module.ecs.execution_role_arn, module.ecs.task_role_arn]
}
