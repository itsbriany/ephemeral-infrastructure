# Ephemeral Environments Roadmap

This is the authoritative implementation sequence. Each milestone ends at a mandatory manual
Lucidchart checkpoint. Work on the next milestone begins only after the project owner confirms that
the diagram for the current architecture is complete.

## Milestone 0 — Project foundation and architectural baseline

**Status:** Complete; architecture checkpoint confirmed.

Establish the GitHub repository, CDK/Python layout, lifecycle model, application-profile boundary,
naming and tagging rules, ADRs, tests, CI, and contributor guidance. Synthesis must create no AWS
resources.

**Done when:** the repository is published, tests and synthesis pass, commit identity is verified,
and the Milestone 0 Lucidchart checkpoint is confirmed.

## Milestone 1 — Lifecycle model and local API contract

**Status:** Complete; architecture checkpoint confirmed.

Implement the four API operations with local persistence and a fake provisioner. Demonstrate
asynchronous creation, status polling, approved application selection, idempotency, and rejected
invalid transitions without touching AWS.

**Done when:** contract tests show one request moving through a simulated lifecycle and duplicate
requests cannot create duplicate environments.

## Milestone 2 — Minimal persistent AWS control plane

**Status:** Implementation complete and synthesized; deployment and architecture checkpoint pending.

Deploy API Gateway, Lambda, DynamoDB, CloudWatch retention, and narrow IAM permissions. Persist
environment requests and protect updates with DynamoDB conditions. Do not create ECS workloads yet.

**Done when:** the deployed API safely creates and retrieves registry records and emits correlated,
non-sensitive logs.

## Milestone 3 — One manually launched disposable environment

Build the Hello Environment container, publish an immutable image to ECR, and create one temporary
ECS/Fargate environment through a versioned CloudFormation template. Measure creation, deletion, and
routing cost before recording the shared-versus-per-environment routing choice.

**Done when:** the workload is healthy and reachable, stack deletion removes all temporary resources,
and no shared resource is accidentally owned by the temporary stack.

## Milestone 4 — Automated provisioning workflow

Connect the API and registry to a Step Functions workflow that creates the approved CloudFormation
stack, waits without a long-running Lambda, verifies health, records outputs, and compensates after
failure.

**Done when:** an API request returns immediately and polling eventually exposes either a verified
endpoint or a meaningful failure with cleanup initiated.

## Milestone 5 — Verified teardown and expiration

Add an independent destruction workflow, manual termination, one-time EventBridge schedules,
session duration from readiness, maximum age from request time, cleanup ownership, and verified stack
absence before quota release.

**Done when:** manual and scheduled termination converge safely and failed deletion remains visible as
`CLEANUP_FAILED`.

## Milestone 6 — Quotas, concurrency, and abuse protection

Enforce approved profiles, global and visitor capacity, cooldowns, throttling, maximum resource sizes,
maximum lifetime, visitor verification, an administrative launch kill switch, and cost alerts.

**Done when:** concurrent and abusive requests cannot bypass hard provisioning limits, and public
input cannot select arbitrary infrastructure.

## Milestone 7 — Reconciliation and orphan recovery

Periodically compare the environment registry with tightly scoped AWS resource inventory. Detect
expired, stuck, missing, and orphaned resources; retry safe cleanup; retain evidence; and alert on
unresolved failures.

**Done when:** injected workflow failures and a controlled test orphan are repaired without selecting
unrelated AWS resources.

## Milestone 8 — Public DNS, TLS, and network hardening

Configure the selected routing design, wildcard environment DNS, ACM certificates, Cloudflare-to-AWS
TLS behavior, security groups, restricted task roles, and an explicit outbound connectivity policy.

**Done when:** every ready environment receives a working HTTPS endpoint and its routing resources are
removed during teardown.

## Milestone 9 — Visitor frontend

Build the static React/TypeScript/HeroUI client for application selection, launch confirmation,
status polling, readiness, failure display, countdown, and early termination. Host it privately in S3
behind CloudFront Origin Access Control.

**Done when:** a visitor can complete the lifecycle without AWS credentials and browser refresh can
recover current state.

## Milestone 10 — CI/CD, observability, and operational readiness

Automate tests, scans, image publishing, CDK synthesis, versioned template publishing, and controlled
deployments. Add dashboards, alarms, structured logs, operational runbooks, cost review, and teardown
drills.

**Done when:** releases are reproducible from GitHub, artifacts are traceable in environment records,
and a controlled failure triggers a useful alarm and recovery procedure.

## Milestone 11 — First real application profile

Onboard a constrained MythWeaver demonstration using synthetic data, limited integrations, immutable
artifacts, application-specific readiness, and reliable teardown. Keep proprietary source in its own
repository when appropriate.

**Done when:** the real application uses the generic lifecycle without leaking application-specific
concerns into the control plane.

## Milestone 12 — Provider abstraction assessment

Use evidence from the completed AWS implementation to identify the stable provider interface, isolate
AWS adapters, and map concepts to Azure and GCP. Do not deploy a second provider without a separate
decision.

**Done when:** API clients remain provider-neutral while AWS-native implementation details retain
clear ownership boundaries.

## Checkpoint questions for every milestone

1. What new component or responsibility was introduced?
2. Why does it exist, and what simpler alternative was rejected?
3. Which data, control, trust, and failure flows changed?
4. Which resources are persistent, shared, or ephemeral?
5. What evidence proves the milestone works?
6. What limitation or risk intentionally remains for the next milestone?
