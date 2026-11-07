# ADR 0002: Synthesize CDK Templates Before Runtime

- **Status:** Accepted
- **Date:** 2026-11-07

## Context

Running the CDK CLI inside a request-handling Lambda would bundle development tooling into the
runtime and broaden its permissions and failure surface.

## Decision

Use CDK during development and CI to synthesize versioned CloudFormation templates. Runtime
orchestration will submit only approved templates with validated parameters through AWS APIs.

## Consequences

Infrastructure compilation and lifecycle execution are separate. Artifact versioning becomes part of
the release process, while public requests cannot provide arbitrary templates.
