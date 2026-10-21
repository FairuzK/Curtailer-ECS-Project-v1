resource "aws_ecr_repository" "this" {
  name                 = var.name
  image_tag_mutability = "MUTABLE" # bootstrap uses :latest; CI pushes unique SHA tags
  force_delete         = true      # lets `terraform destroy` remove a repo that still has images

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Keep storage cost near zero: retain only the 10 most recent images.
resource "aws_ecr_lifecycle_policy" "this" {
  repository = aws_ecr_repository.this.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}
