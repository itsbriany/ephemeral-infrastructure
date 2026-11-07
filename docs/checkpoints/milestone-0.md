# Milestone 0 Architecture Checkpoint

**Status:** Awaiting the project owner's Lucidchart confirmation.

Do not begin Milestone 1 until this checkpoint is confirmed.

## What to draw

Create three large boundaries only:

1. Presentation layer
2. Persistent control plane
3. Ephemeral application environments

Show an arrow from presentation to the control plane and another from the control plane to ephemeral
environments. Label the second arrow with `approved profile + versioned template parameters`.

Use a legend to distinguish:

- persistent resources;
- shared resources;
- ephemeral resources;
- future/not-yet-implemented components.

Do not add detailed AWS services yet. Milestone 0 has only a synthesized, empty control-plane stack
boundary and provider-neutral domain rules.

## Be ready to explain

- Why the control plane outlives all visitor environments.
- Why the API-facing lifecycle does not expose CloudFormation states.
- Why CDK synthesis occurs before runtime provisioning.
- Why AWS is first without claiming the implementation is already multi-cloud.
- Why ECS/Fargate was selected and Kubernetes was deferred.
- Why shared and ephemeral ownership must be visually distinct.
- Why `ca-central-1` is the default and `us-east-1` may appear later for CloudFront certificates.

## Evidence to review

- Unit tests enforce lifecycle, profile, naming, and tag invariants.
- A synthesis assertion proves Milestone 0 defines no AWS resources.
- CI repeats linting, formatting, tests, and synthesis.
- ADRs preserve the reasons behind the initial choices.
