# ADR 0009: Use Operation-Specific Lambda Adapters Behind an HTTP API

- **Status:** Accepted
- **Date:** 2026-11-08

## Context

Milestone 2 needs a small durable API while keeping public input, persistence permissions, logging,
and future orchestration boundaries easy to explain and audit.

## Decision

Use API Gateway HTTP API with one Python Lambda function for each operation: list applications,
create an environment, retrieve an environment, and request termination. Give each function a
separate execution role containing only its required DynamoDB actions and writes to its own retained
log group. Keep the provider-neutral lifecycle model separate from the AWS event and persistence
adapters.

## Consequences

The route-to-permission relationship is explicit, and a compromised read function cannot mutate the
registry. Four functions and roles create more CloudFormation resources than a single multipurpose
handler. Shared source is packaged with each function, which is acceptable at this scale and can be
revisited if deployment size or build time becomes material.
