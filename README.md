# URL Shortener on AWS ECS 

A small Flask URL shortener deployed to **AWS ECS ** behind an **ALB with HTTPS**, built as a DevOps portfolio project:
containerised with a hardened multi-stage Dockerfile, provisioned with modular **Terraform**, and deployed by **GitHub Actions using OIDC** (no long-lived AWS keys) with post-deploy verification and automatic rollback. 

## Architecture

```mermaid
flowchart LR
    user([User]) -->|HTTPS| r53[Route 53] --> alb[ALB + ACM cert]
    subgraph vpc[VPC - 2 public subnets]
        alb -->|8000, only from ALB SG| task[Fargate task<br/>Flask + gunicorn, non-root]
    end
    ecr[(ECR)] -.-> task
    task -.-> cw[(CloudWatch Logs)]
    dev([git push]) --> gh[GitHub Actions] -->|OIDC| iam[IAM role]
    gh -->|push :sha| ecr
    gh -->|deploy + verify /version| task
```
