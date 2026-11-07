# Environment Lifecycle

The lifecycle is provider-neutral. AWS orchestration introduced later must enforce these transitions
rather than exposing CloudFormation states to API clients.

```text
REQUESTED -> PROVISIONING -> VERIFYING -> READY
    |             |             |          |
    +-------------+-------------+----------+----> TERMINATING -> DESTROYED
                  |             |                       |
                  +-------------+-> PROVISIONING_FAILED |
                                      |                 v
                                      +----------> CLEANUP_FAILED
                                                       |
                                                       +-> TERMINATING (retry)
```

## Invariants

- `DESTROYED` is terminal.
- A failed provisioning attempt still requires cleanup ownership.
- `CLEANUP_FAILED` retains evidence and can retry through `TERMINATING`.
- A request must never skip directly to `READY`.
- A deletion request does not prove destruction; the provider must confirm resource absence.
- Session expiration is calculated from readiness, while maximum infrastructure age is calculated
  from the original request.

The executable transition table lives in `src/ephemeral_environments/lifecycle.py`. In Milestone 1,
the fake provisioner uses conditional updates so an early termination request prevents later
provisioning steps from advancing the record.
