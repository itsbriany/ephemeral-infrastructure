# Ephemeral Environments

An AWS-first platform for provisioning, observing, expiring, and destroying isolated short-lived
application demonstrations.

The platform is both portfolio infrastructure and a standalone cloud-engineering case study. Its
first target is a small, reliable AWS implementation; Azure and Google Cloud are future evaluation
targets, not current deliverables.

## Current status

**Milestone 0: Project foundation and architectural baseline — awaiting architecture checkpoint.**

Milestone 0 intentionally deploys no AWS resources. The CDK application synthesizes a control-plane
stack boundary with outputs only so the structure and validation pipeline can be established safely.

## Architectural boundaries

1. **Presentation layer** — a future static React client for requesting and monitoring demos.
2. **Persistent control plane** — the future asynchronous API and lifecycle coordinator.
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
└── tests/                   Fast unit and synthesis assertions
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

## Deployment policy

No AWS deployment is authorized by repository setup or by a successful synthesis. Deployment begins
only in a later milestone and requires an explicit review of the generated changes.
