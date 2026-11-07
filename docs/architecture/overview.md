# Architecture Baseline

Milestone 0 defines boundaries without creating cloud resources.

```text
+----------------------+       +---------------------------+
| Presentation layer   | ----> | Persistent control plane  |
| Future static client |       | Future API + orchestration|
+----------------------+       +-------------+-------------+
                                            |
                                            | approved application profile
                                            | versioned template + parameters
                                            v
                              +-----------------------------+
                              | Ephemeral environment       |
                              | One temporary workload      |
                              | owned by one stack          |
                              +-----------------------------+
```

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

## Deliberately absent in Milestone 0

- No AWS account resources or bootstrap operation
- No API Gateway, Lambda, DynamoDB, Step Functions, ECS, ECR, or load balancer
- No public endpoints, DNS records, or certificates
- No production application container
- No Azure or GCP implementation
