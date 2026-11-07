# ADR 0007: Start the Platform as One Repository

- **Status:** Accepted
- **Date:** 2026-11-07

## Context

The control plane, generic templates, sample workload, and future frontend will evolve together during
the first lifecycle implementation. Premature repository separation would add release coordination
without established independent ownership.

## Decision

Keep generic platform components in one public repository. Real applications may remain in separate,
potentially private repositories and publish immutable artifacts consumed through approved profiles.

## Consequences

Cross-component changes are initially simpler. A component can be extracted later when it gains an
independent release cadence, access boundary, or ownership model.
