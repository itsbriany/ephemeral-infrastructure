# Architecture Through Milestone 1

Milestone 1 implements the control-plane contract locally without creating cloud resources.

```text
+---------------+      +------------------+      +-------------------+
| Local caller  | ---> | FastAPI routes   | ---> | Lifecycle service |
+---------------+      +------------------+      +---------+---------+
                                                        / \
                                                       /   \
                                                      v     v
                                           +-------------+ +------------------+
                                           | In-memory   | | Async work queue |
                                           | registry    | +--------+---------+
                                           +-------------+          |
                                                                    v
                                                           +------------------+
                                                           | Fake provisioner |
                                                           +------------------+
                                                                    |
                                                                    v
                                                        Simulated state changes
```

The service accepts only an application ID from the approved catalog. It atomically reserves an
environment record, then queues work and returns `202 Accepted`. The fake provisioner advances that
record through the same provider-neutral lifecycle that later AWS orchestration must enforce. A
termination request atomically changes the record to `TERMINATING` before destruction work is queued,
so provisioning and termination cannot both advance the same state.

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

## Deliberately absent through Milestone 1

- No AWS account resources or bootstrap operation
- No API Gateway, Lambda, DynamoDB, Step Functions, ECS, ECR, or load balancer
- No public endpoints, DNS records, or certificates
- No durable records, authentication, quotas, or multi-process coordination
- No production application container
- No Azure or GCP implementation
