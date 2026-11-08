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

The executable transition table lives in `src/ephemeral_environments/lifecycle.py`. The Milestone 1
fake provisioner uses conditional in-memory updates. The Milestone 2 AWS adapter uses a DynamoDB
condition to ensure termination can update only an eligible current state. Creation records remain
`REQUESTED`, and termination records remain `TERMINATING`, because real orchestration and verified
cleanup are intentionally deferred.
