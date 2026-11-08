# ADR 0008: Use One DynamoDB Registry with Transactional Idempotency

- **Status:** Accepted
- **Date:** 2026-11-08

## Context

Environment requests must survive process restarts, concurrent retries must not create duplicates,
and lifecycle changes must not overwrite a newer state. Milestone 2 needs these guarantees before a
real provisioner exists.

## Decision

Use one on-demand DynamoDB table with a string partition key. Store environment records under
`ENVIRONMENT#<environment-id>` and idempotency markers under a SHA-256-derived
`IDEMPOTENCY#<digest>` key. Create both items in one transaction with `attribute_not_exists`
conditions. Read retries consistently and return the original environment. Move eligible records to
`TERMINATING` with a conditional update.

Retain the table if the stack is removed, use AWS-managed encryption, and enable seven-day
point-in-time recovery. Do not expire idempotency markers until a bounded retention policy is proven
alongside cleanup and quota behavior.

## Consequences

Retries converge on one environment record and the raw idempotency key is not stored. Conditional
writes expose races instead of silently losing updates. Each creation consumes two transactional
writes, and the table contains two entity types that operators must understand. A later retention
policy will be needed to bound marker storage.
