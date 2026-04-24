# ServiceNow Integration Acceptance
- Idempotent sync endpoint creates one PR per request/version.
- Merge callback updates SN state to implemented_active.
- Reconciler detects drift and repair candidates.
