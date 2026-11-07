# Repository Working Agreement

These instructions apply to the entire repository.

## Project intent

Build an interview-ready platform for isolated, short-lived application environments. Work in
small milestones that leave behind evidence, an explainable architecture change, and a manual
Lucidchart checkpoint.

## Milestone gate

- Implement only the active milestone in `ROADMAP.md`.
- At the end of every milestone, stop before beginning the next milestone.
- project owner owns the Lucidchart diagrams. Provide component lists, flows, tradeoffs, and small ASCII
  sketches, but do not create or maintain the Lucidchart artifact.
- Do not proceed until project owner confirms the current architecture is documented in Lucidchart.

## Source control

- All project repositories must be hosted on GitHub.
- Before every commit, verify the local Git author identity matches the approved private configuration.
- Use focused commits with messages that explain the architectural outcome.
- Do not commit secrets, generated cloud assemblies, local environments, or credentials.

## AWS safety

- Do not deploy, update, or destroy AWS resources without explicit approval in the current task.
- Prefer synthesis and assertions before deployment.
- Public callers may select only approved application profiles. Never accept arbitrary templates,
  images, IAM policies, or resource specifications.
- Separate persistent, shared, and ephemeral resources in code, ownership, names, and tags.
- Make lifecycle operations idempotent and verify asynchronous deletion before releasing quota.
- Treat cost containment as a security property: bounded lifetime, capacity, and resource sizes are
  mandatory before public launches.

## Engineering standards

- Use Python 3.12, Node.js 24, AWS CDK v2, `uv`, `pytest`, and `ruff` unless an ADR changes the
  choice.
- Keep the provider-neutral lifecycle domain separate from AWS adapters and CDK constructs.
- Favor direct, testable code over speculative abstraction.
- Add or update tests with behavior changes.
- Use immutable container image digests for deployable application profiles.
- Emit structured, non-sensitive logs with environment correlation identifiers.
- Update ADRs when a choice changes architecture, security, cost, or operational behavior.

## Local validation

Run before proposing a commit:

```bash
uv sync --locked --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest -v
uv run python app.py
```

Milestone 0 synthesis must contain no AWS resources.
