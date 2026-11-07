# Hello Environment Contract

`hello-environment` is the first approved application profile. Milestone 0 defines its contract but
does not yet build or publish the container.

The future container must:

- listen on TCP port `8080`;
- expose `GET /health` and return success only when ready;
- expose a small page that displays its environment ID and template version;
- require no database, secrets, AWS permissions, or outbound network access;
- run as a non-root user with a read-only filesystem where practical;
- shut down cleanly on `SIGTERM`;
- produce concise structured logs without sensitive values;
- build deterministically and be referenced by immutable image digest.

The intentionally small workload isolates platform behavior from application complexity during the
first real provisioning exercise.
