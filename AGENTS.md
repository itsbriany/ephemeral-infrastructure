# Repository Working Agreement

These instructions apply to the entire repository.

## Project intent

Build an interview-ready platform for isolated, short-lived application environments. Work in
small milestones that leave behind evidence, an explainable architecture change, and a manual
Lucidchart checkpoint.

## Milestone gate

- Implement only the active milestone in `ROADMAP.md`.
- At the end of every milestone, stop before beginning the next milestone.
- The project owner owns the Lucidchart diagrams. Provide component lists, flows, tradeoffs, and
  small ASCII sketches, but do not create or maintain the Lucidchart artifact.
- Do not proceed until the project owner confirms the current architecture is documented in
  Lucidchart.

## Source control

- All project repositories must be hosted on GitHub.
- Before every commit, verify the local Git author identity matches the project owner's approved
  private configuration. Do not publish that identity in repository documentation.
- Use focused commits with messages that explain the architectural outcome.
- Do not commit generated cloud assemblies or local virtual environments.
- Do not publish personal location, contact information, account details, or other private context in
  documentation, examples, comments, logs, fixtures, or commit messages.

## Secrets and credentials

- Never commit or publish credentials or secret material, including cloud access keys, API tokens,
  passwords, private keys, session tokens, cookies, certificates containing private keys, connection
  strings, local environment files, or credential-provider configuration.
- Use obviously synthetic, nonfunctional values in tests, fixtures, examples, and documentation.
  Never copy a real value and partially redact it.
- Load local secrets from environment variables or ignored local files. Deployed secrets must come
  from an approved secret manager and must not be embedded in CDK context, CloudFormation templates,
  source code, container images, build artifacts, logs, or workflow definitions.
- Before every commit, inspect the staged diff and run the repository's secret scan when one is
  available. Never bypass a secret-scanning or push-protection alert without confirming the match is
  synthetic and documenting why it is safe.
- If a secret may have been exposed, stop normal work immediately. Notify the project owner, revoke
  or rotate the credential first, then remove it from reachable history and follow the hosting
  provider's cache-purge process. A deletion commit alone is not remediation.

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

Also inspect `git diff --cached` for private information and credential material before committing.

Milestone 0 synthesis must contain no AWS resources.
