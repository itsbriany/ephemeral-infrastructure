# ADR 0001: Implement AWS Before Additional Providers

- **Status:** Accepted
- **Date:** 2026-11-07

## Context

The lifecycle should eventually admit provider-specific implementations, but simultaneous AWS,
Azure, and GCP development would multiply untested abstractions before one reliable lifecycle exists.

## Decision

Complete the first implementation on AWS. Keep public lifecycle contracts provider-neutral and defer
additional providers until the AWS implementation supplies evidence about the true abstraction seam.

## Consequences

AWS-native services can be used well. Multi-cloud claims remain conceptual until another provider is
actually implemented.
