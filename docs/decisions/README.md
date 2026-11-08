# Architecture Decision Records

ADRs capture choices that materially affect architecture, security, cost, or operations.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-aws-first.md) | Implement AWS before additional providers | Accepted |
| [0002](0002-synthesize-templates-before-runtime.md) | Synthesize CDK templates before runtime | Accepted |
| [0003](0003-ecs-fargate-runtime.md) | Begin with ECS/Fargate for interactive workloads | Accepted |
| [0004](0004-asynchronous-api.md) | Use an asynchronous lifecycle API | Accepted |
| [0005](0005-no-initial-kubernetes.md) | Do not introduce Kubernetes initially | Accepted |
| [0006](0006-primary-region.md) | Default regional workloads to `ca-central-1` | Accepted |
| [0007](0007-platform-monorepo.md) | Start the platform as one repository | Accepted |
| [0008](0008-dynamodb-registry.md) | Use one DynamoDB registry with transactional idempotency | Accepted |
| [0009](0009-operation-specific-lambdas.md) | Use operation-specific Lambda adapters behind HTTP API | Accepted |

An accepted decision can be replaced by a later ADR when implementation evidence changes the
tradeoff. Do not silently rewrite the historical reason for a choice.
