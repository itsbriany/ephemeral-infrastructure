# ADR 0006: Default Regional Workloads to ca-central-1

- **Status:** Accepted
- **Date:** 2026-11-07

## Context

The platform needs a concrete regional default for reproducible synthesis, service evaluation, and
cost analysis. The current feature set does not require a different region.

## Decision

Default persistent regional resources and ephemeral workloads to `ca-central-1`. Keep the value
configurable. Permit `us-east-1` only where a global AWS service requires it, such as a future ACM
certificate for a custom CloudFront hostname.

## Consequences

Regional assumptions are explicit and can be measured. Service availability and pricing must be
rechecked before each later milestone that introduces a new AWS service.
