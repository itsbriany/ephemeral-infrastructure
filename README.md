# Ephemeral Environments

An AWS-first platform for provisioning, observing, expiring, and destroying isolated short-lived
application demonstrations.

The platform is both portfolio infrastructure and a standalone cloud-engineering case study. Its
first target is a small, reliable AWS implementation; Azure and Google Cloud are future evaluation
targets, not current deliverables.

## Current status

**Milestone 2: Minimal persistent AWS control plane — implemented and synthesized; not deployed.**

The CDK stack defines an API Gateway HTTP API, operation-specific Python Lambda functions, a durable
DynamoDB registry, retained logs, route throttling, and narrowly scoped IAM permissions. Creation is
transactionally idempotent, while termination uses a conditional lifecycle update. No AWS deployment
or workload resources have been created. The Milestone 1 FastAPI simulation remains available for
local lifecycle demonstrations.

## Architectural boundaries

1. **Presentation layer** — a future static React client; local callers currently use the HTTP API.
2. **Control plane** — a persistent AWS API and registry, plus a local lifecycle simulator.
3. **Ephemeral environments** — temporary application resources owned by one environment stack.

See [the architecture overview](docs/architecture/overview.md), [the roadmap](ROADMAP.md), and
[the decision records](docs/decisions/README.md).

## Repository layout

```text
.
├── .github/workflows/       Validation automation
├── docs/architecture/       Current architecture in prose
├── docs/checkpoints/        Manual milestone handoff prompts
├── docs/decisions/          Architecture decision records
├── sample-app/              Contract for the first disposable workload
├── src/                     Domain and CDK code
└── tests/                   Unit, API contract, and synthesis assertions
```

The real demo applications may remain in separate private repositories. This repository owns the
generic lifecycle, infrastructure templates, sample workload, and eventually the visitor frontend.

## Local validation

Requirements: Python 3.12, Node.js 24, and `uv`.

```bash
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest -v
uv run python app.py
```

The final command synthesizes `cdk.out/`; it does not deploy anything.

## Run the local lifecycle simulator

Start the local server:

```bash
uv run uvicorn ephemeral_environments.api:app --reload
```

The interactive API description is available at `http://127.0.0.1:8000/docs`. A minimal request and
polling flow is:

```bash
curl http://127.0.0.1:8000/applications

curl -i -X POST http://127.0.0.1:8000/environments \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: local-demo-001' \
  -d '{"applicationId":"hello-environment"}'

curl http://127.0.0.1:8000/environments/<environment-id>

curl -i -X DELETE http://127.0.0.1:8000/environments/<environment-id>
```

The returned `example.invalid` endpoint is deliberately non-resolving. It proves when an endpoint
becomes visible in the lifecycle without pretending that a workload exists.

## Deployment policy

No AWS deployment is authorized by repository setup or by a successful synthesis. Every deployment,
update, and destruction operation requires explicit approval after review of the generated changes.
