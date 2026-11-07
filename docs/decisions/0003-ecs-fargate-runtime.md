# ADR 0003: Begin With ECS/Fargate for Interactive Workloads

- **Status:** Accepted
- **Date:** 2026-11-07

## Context

The first workloads are long-running interactive HTTP applications that need health checks, routing,
logs, and predictable teardown without host management.

## Decision

Use an ECS service with one Fargate task as the initial workload model. Revisit direct tasks or other
runtimes only when an application profile has different operational requirements.

## Consequences

The platform avoids managing EC2 hosts, but pays for running task resources and must explicitly solve
networking, service readiness, and routing.
