# Naming and Tagging Standard

Names use lowercase kebab-case:

```text
ephemeral-environments-<component>[-<environment-id>]
```

Every managed resource will carry these tags when supported:

| Tag | Purpose |
| --- | --- |
| `platform` | Limits inventory and reconciliation to this platform. |
| `component` | Identifies the owning architectural component. |
| `resource-scope` | Distinguishes `persistent`, `shared`, and `ephemeral`. |
| `managed-by` | Records the infrastructure management mechanism. |
| `cost-center` | Supports cost allocation and reporting. |
| `environment-id` | Required only for environment-owned resources. |

Later milestones will add creation and expiration metadata where the target AWS resource supports
tags. Tags aid discovery and safety checks, but deletion logic must also verify account, region,
stack ownership, and expected name prefixes.
