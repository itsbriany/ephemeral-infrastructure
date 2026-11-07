# Milestone 1 Architecture Checkpoint

**Status:** Awaiting the project owner's Lucidchart confirmation.

Do not begin Milestone 2 until this checkpoint is confirmed.

## What to add to the Milestone 0 diagram

Expand the control-plane boundary into these components:

1. FastAPI routes
2. Lifecycle service
3. Approved application catalog
4. In-memory environment registry
5. Asynchronous work queue
6. Fake provisioner

Keep the presentation layer and real ephemeral environment boundary marked as future work. Draw the
registry and queue inside one local process, and label them `Milestone 1 only / not durable`.

```text
Local caller
     |
     | HTTP: list, create, get, terminate
     v
FastAPI routes ---> Lifecycle service ---> In-memory registry
                           |                       ^
                           | enqueue               | conditional state update
                           v                       |
                    Async work queue ------> Fake provisioner
```

Add a separate arrow from the approved application catalog to the lifecycle service. The caller sends
only an `applicationId`; it cannot provide a container image, template, IAM policy, or resource size.

## Label the two important request flows

Creation:

```text
POST + Idempotency-Key -> reserve REQUESTED -> enqueue -> return 202
worker -> PROVISIONING -> VERIFYING -> READY
client -> GET until terminal or READY state
```

Termination:

```text
DELETE -> atomically mark TERMINATING -> enqueue -> return 202
worker -> DESTROYED
client -> GET to verify destruction
```

## Be ready to explain

- Why a `202 Accepted` response means work started, not that an environment is ready.
- Why status polling is a separate operation from creation.
- How one idempotency key maps retries to exactly one environment record.
- Why the lock makes reservation and state updates atomic inside one process.
- How conditional updates stop the fake provisioner after an early termination request.
- Why the API accepts an approved application ID instead of infrastructure definitions.
- Why the API, service, repository, and provisioner are separate even in a small local implementation.
- Why in-memory state and an in-process queue are teaching tools, not production persistence.
- Which components DynamoDB and AWS orchestration will replace in Milestone 2 and later milestones.

## Evidence to review

- Contract tests exercise all four operations and the complete simulated lifecycle.
- A duplicate creation request returns the same environment ID and does not create another record.
- Invalid public input, missing records, and idempotency conflicts are rejected.
- Existing lifecycle tests reject invalid state transitions and keep `DESTROYED` terminal.
- CDK synthesis still proves that the project creates no AWS resources.

## Intentionally deferred

- Durable storage, conditional writes across processes, and recovery after restart
- API Gateway, Lambda, DynamoDB, Step Functions, IAM, and CloudWatch
- Authentication, visitor identity, quotas, throttling, and abuse controls
- A real container, reachable endpoint, health check, and verified cloud teardown
