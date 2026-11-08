# Architecture Through Milestone 2

Milestone 2 makes the request registry durable and places the four public operations behind an AWS
HTTP API. The local Milestone 1 simulator remains a separate teaching and contract-testing path.

```text
Caller -> API Gateway HTTP API -> operation-specific Lambda -> DynamoDB registry
                    |                       |
                    v                       v
             access log group       function log groups
```

The API accepts only an application ID from the approved catalog. Creation atomically writes an
environment record and a hashed idempotency marker, then returns `202 Accepted`. Termination uses a
conditional update to move an eligible record to `TERMINATING`. No cloud provisioner consumes these
states yet: records remain `REQUESTED` or `TERMINATING` until later workflow milestones.

Each operation has its own Lambda function and execution role. This makes the route-to-permission
mapping visible: listing applications needs no table access; creation can read and transact; retrieval
can read; termination can read and update. API and function log groups retain non-sensitive,
correlated records for 30 days.

## Ownership rules

- Persistent resources live independently of visitor environments.
- Shared resources may be referenced by temporary stacks but must never be owned or deleted by them.
- Ephemeral resources belong to exactly one environment ID and must carry ownership tags.
- The control plane accepts an application ID, never an arbitrary infrastructure definition.
- Runtime provisioning will consume pre-synthesized, versioned CloudFormation templates.

## Initial regional model

Regional control-plane and workload resources default to `ca-central-1`. A later CloudFront-backed
frontend may require an ACM certificate in `us-east-1`; that exception does not move the application
workloads out of the primary region.

## Deliberately absent through Milestone 2

- No deployed AWS resources without a separate explicit deployment approval
- No Step Functions, ECS, ECR, load balancer, or ephemeral application environment
- No DNS records, certificates, or visitor frontend
- No authentication, visitor identity, quotas, or comprehensive abuse controls
- No production application container
- No Azure or GCP implementation
