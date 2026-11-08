# Milestone 2 Architecture Checkpoint

**Status:** Implementation is complete and synthesized. AWS deployment and the project owner's
Lucidchart confirmation are pending.

Do not begin Milestone 3 until this checkpoint is confirmed and Milestone 2 deployment evidence has
been addressed under an explicitly approved deployment task.

## Components to add

| Component | Purpose |
| --- | --- |
| API Gateway HTTP API | Owns the four HTTP routes, invokes the matching Lambda, throttles traffic, and emits access logs. |
| List applications Lambda | Returns only approved profiles and has no DynamoDB permission. |
| Create environment Lambda | Validates the application and idempotency key, then requests an atomic reservation. |
| Get environment Lambda | Reads one environment so a caller can poll durable state. |
| Terminate environment Lambda | Conditionally changes an eligible record to `TERMINATING`. |
| DynamoDB registry | Durably stores environment records and hashed idempotency markers. |
| Function execution roles | Give each Lambda only its route-specific table and logging actions. |
| CloudWatch log groups | Retain correlated API and function logs for 30 days without request bodies or idempotency keys. |

All of these resources are persistent control-plane resources. The local FastAPI process remains a
development simulator, not part of the deployed AWS request path. No shared workload or ephemeral
application resources exist yet.

## Suggested diagram

```text
Caller
  |
  v
API Gateway HTTP API --------------------> API access logs
  |
  +-- GET /applications -----------------> List Lambda (no table access)
  +-- POST /environments ----------------> Create Lambda -- Get + TransactWrite --+
  +-- GET /environments/{id} ------------> Get Lambda ---- GetItem ------------->| DynamoDB
  +-- DELETE /environments/{id} ---------> Terminate Lambda -- Get + Update ---->|
                                               |
                                               +----------------> function logs
```

Draw a persistent control-plane boundary around API Gateway, the four Lambdas, DynamoDB, IAM roles,
and log groups. Leave the presentation layer and ephemeral environment boundary dashed and labeled
as future milestones.

## Creation flow

```text
POST applicationId + Idempotency-Key
  -> API Gateway assigns request ID
  -> Create Lambda validates approved application
  -> DynamoDB transaction conditionally writes:
       ENVIRONMENT#<id> = REQUESTED
       IDEMPOTENCY#<hash> -> <id>
  -> 202 Accepted + environment ID

Retry with same key
  -> transaction condition fails
  -> consistent read of marker and environment
  -> same environment ID + replay header
```

## Termination flow

```text
DELETE /environments/<id>
  -> Terminate Lambda
  -> conditional DynamoDB update from an eligible current status
  -> TERMINATING + 202 Accepted

Retry after TERMINATING
  -> conditional update does not apply
  -> read current record
  -> return the same TERMINATING state
```

## Be ready to explain

- DynamoDB replaces only the in-memory registry; Milestone 2 does not replace the fake provisioner
  with a cloud provisioner.
- A transaction prevents an environment record from existing without its idempotency marker, or the
  reverse.
- Hashing the marker key avoids storing the caller-supplied idempotency value, but the hash is an
  identifier, not encryption.
- Conditional writes protect state when multiple Lambda instances act concurrently.
- Separate Lambdas cost more resources but make least privilege and ownership easier to see.
- The table is retained because deleting a control-plane stack must not silently erase lifecycle
  evidence.
- `REQUESTED` and `TERMINATING` intentionally stall until later provisioning and teardown workflows.
- HTTP throttling is a guardrail, not authentication or complete abuse protection.

## Evidence

- Unit tests emulate duplicate and conflicting writes, conditional termination, and missing records.
- Handler tests prove input rejection, response contracts, and log redaction.
- CDK assertions prove exact resource counts, routes, log retention, table protection, throttling,
  least-privilege actions, and the absence of ECS or Step Functions.
- Synthesis produces a reviewable CloudFormation template without changing AWS.

## Intentionally deferred

- A live AWS deployment and smoke-test evidence
- Authentication, visitor identity, quotas, cooldowns, and a launch kill switch
- Automated provisioning, failure compensation, verified teardown, and reconciliation
- ECR images, ECS tasks, load balancing, DNS, TLS, and a real application endpoint
