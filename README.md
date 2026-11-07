# Ephemeral Environments

An AWS-first platform for provisioning, observing, expiring, and destroying isolated short-lived
application demonstrations.

The platform is both portfolio infrastructure and a standalone cloud-engineering case study. Its
first target is a small, reliable AWS implementation; Azure and Google Cloud are future evaluation
targets, not current deliverables.

## Current status

**Milestone 1: Lifecycle model and local API contract — awaiting architecture checkpoint.**

The local FastAPI application now accepts asynchronous environment requests, exposes status polling,
and supports early termination. An in-memory registry and fake provisioner exercise the lifecycle
contract without creating AWS resources. Process restarts intentionally erase all local records.

## Architectural boundaries

1. **Presentation layer** — a future static React client; local callers currently use the HTTP API.
2. **Control-plane contract** — a local asynchronous API, lifecycle service, and process-local registry.
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

## Run the Milestone 1 API

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

No AWS deployment is authorized by repository setup or by a successful synthesis. Deployment begins
only in a later milestone and requires an explicit review of the generated changes.
