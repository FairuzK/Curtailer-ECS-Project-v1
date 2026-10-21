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
## Features
- Multi-stage Docker build, non-root user (uid 10001), health check
- Terraform modules: `network`, `ecr`, `alb`, `acm`, `ecs`, `github_oidc`
- HTTPS with ACM + Route 53 and an HTTP to HTTPS redirect (optional, enabled by setting a domain)
- Least-privilege IAM: separate task execution role and task role; CI role scoped to one repo and branch
- ECS deployment circuit breaker with automatic rollback
- CI: pytest, `terraform fmt`/`validate`, build, push, deploy, then poll `/version` until it equals the commit SHA

## API
| Method | Path | Description |
|---|---|---|
| POST | `/api/shorten` | Body `{"url": "https://..."}`, returns `{"code", "short_url"}` |
| GET | `/<code>` | 302 redirect (increments click count) |
| GET | `/api/links/<code>` | Link stats |
| GET | `/health` | Health check (verifies DB access) |
| GET | `/version` | Deployed git SHA |

## Quick start (local)
```bash
make venv && make test && make run     # http://localhost:8000
# or
make docker-build && make docker-run
```

## Deploy
Follow [GUIDE.md](GUIDE.md): console walkthrough first (sections 5-8), then Terraform (9) and CI/CD (10).

## Design decisions and trade-offs
| Decision | Why | Production alternative |
|---|---|---|
| SQLite | Zero setup, focus on the platform | RDS PostgreSQL (GUIDE section 12) |
| `desired_count = 1` | Each task has its own private DB | Shared DB, then autoscale |
| Public subnets, no NAT | Saves ~$32/month; task SG only admits the ALB | Private subnets + NAT or VPC endpoints |
| Immutable git-SHA image tags | Traceable, rollback-friendly | Same, plus image signing |
| Terraform `ignore_changes = [task_definition]` | CI owns image rollouts, Terraform owns infrastructure | Dedicated deployment tooling |
| Local Terraform state | Simplicity | S3 backend with locking |

## Cost
Roughly $1/day while running (ALB + Fargate + public IPv4 addresses). Destroy when you are not demoing: `cd terraform && terraform destroy`.

## What I'd add next
RDS, autoscaling, WAF, private subnets with VPC endpoints, CloudWatch alarms, remote Terraform state, blue/green deployments.
