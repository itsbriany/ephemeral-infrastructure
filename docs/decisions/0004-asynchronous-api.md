# ADR 0004: Use an Asynchronous Lifecycle API

- **Status:** Accepted
- **Date:** 2026-11-07

## Context

CloudFormation and application readiness take longer than an ordinary HTTP request and can fail after
the initial request has been accepted.

## Decision

Creation returns an environment ID and initial state immediately. Clients retrieve status separately.
Creation and termination operations require idempotency protection.

## Consequences

Clients must handle polling and intermediate states. The API remains responsive, and workflow state
is observable rather than hidden behind a long request.
