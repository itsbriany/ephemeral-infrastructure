# ADR 0005: Do Not Introduce Kubernetes Initially

- **Status:** Accepted
- **Date:** 2026-11-07

## Context

The first platform runs a small number of predefined workloads. Kubernetes would add a persistent
control plane, operational surface, and cost without solving a demonstrated requirement.

## Decision

Use ECS/Fargate and AWS-native orchestration for the initial implementation. Reconsider Kubernetes
only if workload scheduling, portability, or tenancy requirements justify it.

## Consequences

The initial system is smaller and more AWS-specific. The project avoids presenting tool adoption as
an architectural requirement.
