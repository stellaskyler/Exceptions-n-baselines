# GitHub + ServiceNow Exception Management Extension

## Executive summary

This target state preserves **GitHub Enterprise Cloud as the canonical governance/policy layer** and introduces **ServiceNow as the workflow orchestration layer** for exception intake and approvals.

- **GitHub remains system of record** for baseline/control definitions, machine-enforceable exception records, approval evidence pointers, policy state, and enforcement inputs.
- **ServiceNow remains system of workflow** for request intake, task routing, risk/operations coordination, human approvals, SLA tracking, and operational fulfillment.
- **No exception is active for enforcement until a GitHub exception record is merged** into `exception-registry` default branch.
- **ServiceNow approval alone is necessary but not sufficient**; it authorizes record creation, but enforcement keys only off GitHub record state.

Design principle: **workflow in ServiceNow, authority in GitHub, synchronized by deterministic integration contracts**.

---

## Reference architecture

```text
  Requesters / Owners / Risk / Sec / IT Ops
                    |
                    v
      +-----------------------------------------+
      | ServiceNow Exception Workflow           |
      | - intake form                           |
      | - triage/risk tasks                     |
      | - approvals (CAB/risk/security/legal)   |
      | - SLA, escalations, notifications       |
      +--------------------+--------------------+
                           | outbound REST/webhook (approved/updated/revoked)
                           v
      +-----------------------------------------------------+
      | Integration Service (stateless)                     |
      | - correlation/idempotency store                     |
      | - maps SN states <-> GitHub states                  |
      | - calls GitHub App APIs                             |
      | - retries + DLQ + reconciliation API                |
      +--------------------+--------------------------------+
                           |
                           v
+---------------------------------------------------------------+
| GitHub Enterprise Cloud (governance plane)                    |
|  org-governance repos:                                         |
|  - baseline-catalog                                             |
|  - exception-registry  <---- PRs by GitHub App bot             |
|  - policy-engine      <---- reads exception-registry            |
|  - asset-register                                               |
|  - template-factory                                              |
|  - governance-docs                                               |
|                                                                 |
|  GitHub Actions: validation, simulation, merge checks, expiry   |
|  GitHub App: PR creation, status callbacks, signed provenance   |
+----------------------+------------------------------------------+
                       |
                       v
     External governed systems (cloud, SaaS, endpoints, vendors)
      consume policy decisions/checks + evidence pointers
                       |
                       v
      Audit/Evidence/Reporting sinks (SIEM, data warehouse, GRC)
```

---

## System responsibility matrix

| Capability | GitHub | ServiceNow | Integration component | Source of truth |
|---|---|---|---|---|
| Baseline definition | `baseline-catalog` YAML + PR governance | Read-only reference copy/links | Sync metadata for display | **GitHub** |
| Control definition | `baseline-catalog/controls` | Read-only references for form choices | Lookup/cache | **GitHub** |
| Asset metadata | `asset-register` canonical IDs | Operational ownership/context copy for routing | Bi-directional ref check | **GitHub** (authoritative IDs), ServiceNow for assignment queues |
| Request intake | N/A | Native catalog item/form/workflow | Validates required IDs against GitHub API | **ServiceNow** for intake transaction |
| Approval workflow | Approval evidence pointers stored in exception record | Native approvals/tasks/SLAs | Writes approval outcome to GitHub PR body + metadata | **ServiceNow** for human decision workflow; **GitHub** for enforcement-relevant record |
| Exception record | `exception-registry` versioned YAML | Stores linked ticket state | Creates/updates PR via GitHub App | **GitHub** |
| Expiry tracking | Enforced from exception YAML dates | Reminder/escalation + renewal tasks | Reconciliation alarms on drift | **GitHub** for active/inactive status |
| Renewal | New version record/PR in `exception-registry` | Renewal workflow initiation + approvals | Generates renewal PR linked to original | **GitHub** record version; ServiceNow for process |
| Enforcement | `policy-engine` checks active exceptions in GitHub | Shows mirrored compliance status | Status push from GitHub to SN | **GitHub** |
| Audit reporting | Git history, PR approvals, checks, signed artifacts | Workflow timings, task audit, SLA | Unified warehouse feed | **GitHub** for control state, ServiceNow for process metrics |
| Evidence links | Pointer fields in YAML | Attachment repository | Converts attachments to immutable object links | **GitHub pointer + external immutable store** |

---

## System-of-record boundaries (explicit)

### GitHub owns (authoritative)
1. Baseline and control definitions.
2. Exception records and lifecycle state used by enforcement (`draft/submitted/approved/active/expired/revoked`).
3. Approval evidence pointers (not raw large binaries).
4. Policy-engine inputs and decisions.
5. Final “is exception active?” decision.

### ServiceNow owns (authoritative)
1. Intake transaction and request workflow instance.
2. Assignment/routing tasks, escalations, and approval choreography.
3. Operational SLA timers and queue management.
4. Human workflow context (comments, handoffs, operational notes).

### Duplicated vs referenced
- Duplicated (minimal): request title, rationale summary, dates, requester/approver identities, risk score snapshot.
- Referenced: full baseline/control text, full Git exception YAML, evidence binaries, enforcement decisions.
- Rule: if duplicated fields drift, **GitHub wins for enforcement semantics**, ServiceNow wins for workflow bookkeeping.

### Authoritative fields
- `status_active_for_enforcement`: GitHub only.
- `approval_route_status`: ServiceNow only.
- `expiry_effective`: GitHub date in merged exception record.
- `approval_evidence_links`: GitHub pointers (generated from ServiceNow and/or external evidence store).

---

## Detailed exception lifecycle (state machine)

### Canonical lifecycle

| Phase | ServiceNow status | GitHub status | Sync point | Transition condition |
|---|---|---|---|---|
| Intake | `New` | none | SN validates IDs against GitHub refs | Request submitted |
| Triage | `Triaged` | none | Optional draft issue link | Scope/risk complete |
| Risk review | `Risk Assessment` | none | Risk summary frozen | Required assessments done |
| Approval routing | `Awaiting Approval` | `draft` (optional pre-PR) | Integration may create draft PR | All required approvals granted in SN |
| Authorized for codification | `Approved - Pending GitHub` | `submitted` (PR open) | **Create PR in `exception-registry`** | Integration posts PR URL back to SN |
| Policy validation | `Approved - Pending GitHub` | `submitted` | GitHub checks run | Checks + CODEOWNERS approvals pass |
| Active | `Implemented/Active` | `active` | Merge webhook updates SN | PR merged + `valid_from` reached |
| Renewal window | `Renewal Due` | `active` | Scheduled notices both sides | `T-30/T-14/T-7` days |
| Expired | `Expired` | `expired` | GitHub expiry job pushes status | `now > valid_until` |
| Revoked | `Revoked` | `revoked` | Revocation API -> PR/update | Revocation approved |
| Closed | `Closed` | `expired` or `revoked` | Closure sync | Workflow complete |

### Hard control boundary
An SN record in `Approved` **must be mapped to** `Approved - Pending GitHub` until the GitHub PR is merged. No gateway/enforcement consumer may treat it as active earlier.

---

## Canonical data model

## 1) GitHub exception YAML schema (sample)

```yaml
apiVersion: governance/v1
kind: ExceptionRecord
metadata:
  exception_record_id: EXR-2026-000184
  exception_request_id: SN-EXC-0009123
  workflow_instance_id: SNWF-2f9f1c2d-77f5-4fdd-8c67-3f4fb05d17f4
  source_system: servicenow
  created_at: "2026-04-23T11:48:20Z"
  created_by: "servicenow-integration-bot"
spec:
  asset_id: ASSET-REPO-org-cloud-networking-iac
  baseline_id: BL-CLOUD-FOUNDATIONAL
  control_id: CTRL-GH-CODEOWNERS
  scope:
    repositories:
      - org-cloud/networking-iac
  exception_type: temporary_deviation
  rationale: >-
    Monorepo split in progress; CODEOWNERS remap scheduled during migration window.
  risk_statement: "Potential review coverage gap mitigated by mandatory security reviewers."
  compensating_controls:
    - control_id: CTRL-PR-SECURITY-REVIEW-MANDATORY
      validation_ref: "policy-check://security-review-required"
  valid_from: "2026-04-24"
  valid_until: "2026-05-24"
  renewal:
    allowed: true
    max_renewals: 1
    renewal_strategy: new_version_linked
  approvals:
    - approval_id: APR-SEC-00911
      role: security-governance
      approver: "bob@example.com"
      decision: approved
      decided_at: "2026-04-23T10:15:00Z"
    - approval_id: APR-RISK-00442
      role: risk-office
      approver: "carol@example.com"
      decision: approved
      decided_at: "2026-04-23T10:18:00Z"
  evidence_links:
    - type: servicenow_record
      url: "https://company.service-now.com/x_gov_exception.do?sys_id=abc123"
    - type: immutable_object
      url: "s3://evidence-worm/exceptions/SN-EXC-0009123/approval-pack.json"
status:
  lifecycle_state: active
  policy_effective: true
  supersedes: null
  superseded_by: null
```

## 2) ServiceNow exception request schema (sample record payload)

```json
{
  "exception_request_id": "SN-EXC-0009123",
  "workflow_instance_id": "SNWF-2f9f1c2d-77f5-4fdd-8c67-3f4fb05d17f4",
  "request_state": "approved_pending_github",
  "requester": "alice@example.com",
  "requested_for_team": "networking-platform",
  "asset_id": "ASSET-REPO-org-cloud-networking-iac",
  "baseline_id": "BL-CLOUD-FOUNDATIONAL",
  "control_id": "CTRL-GH-CODEOWNERS",
  "exception_type": "temporary_deviation",
  "risk_rating": "medium",
  "business_justification": "Monorepo split requires temporary CODEOWNERS transition.",
  "compensating_controls": ["CTRL-PR-SECURITY-REVIEW-MANDATORY"],
  "requested_valid_from": "2026-04-24",
  "requested_valid_until": "2026-05-24",
  "approval_ids": ["APR-SEC-00911", "APR-RISK-00442"],
  "github": {
    "repo": "org-governance/exception-registry",
    "pull_request_number": 287,
    "pull_request_url": "https://github.com/org-governance/exception-registry/pull/287",
    "exception_record_id": "EXR-2026-000184",
    "merge_commit_sha": null
  },
  "idempotency_key": "SN-EXC-0009123:v3"
}
```

## 3) Correlation model

- `exception_request_id`: generated by ServiceNow, immutable, primary workflow key.
- `exception_record_id`: generated by integration service when creating GitHub record.
- `workflow_instance_id`: ServiceNow execution UUID for end-to-end trace.
- `approval_id`: one per approver decision in ServiceNow; copied into YAML.
- Correlation uniqueness: `(exception_request_id, version)` must map to exactly one GitHub PR and one record version.

---

## Integration design

## Components and mechanism labels
- **ServiceNow workflow/configuration**: intake form, stages, approvals, business rules.
- **External integration service**: orchestration API, idempotency, retries, reconciliation.
- **GitHub App or bot**: authenticated PR creation/status updates in governance repos.
- **GitHub Actions/reusable workflow**: schema validation/policy simulation/auto-expiry.
- **Native GitHub capability**: PR review, CODEOWNERS, protected branches, audit log.

## API and event flows

1. **Inbound SN -> GitHub (create/update exception)**
   - Initiator: ServiceNow Flow Designer action on `approved_pending_github`.
   - Call: `POST /exceptions/sync` to integration service with idempotency key.
   - Integration calls GitHub App installation APIs:
     - create branch
     - write YAML file
     - open PR against `exception-registry`
   - Integration updates ServiceNow with `pull_request_url` + status.

2. **Outbound GitHub -> ServiceNow (merge/reject/validation results)**
   - Initiator: GitHub webhooks (`pull_request`, `check_run`, `push`).
   - Integration receives event, maps to request state, updates SN record.

3. **Scheduled reconciliation (bidirectional read/repair)**
   - Initiator: hourly/daily job in integration service.
   - Compares ServiceNow approved records vs GitHub merged record presence/state.
   - Opens repair task and/or retries sync where drift exists.

## Idempotency strategy
- All mutating SN->integration calls include `idempotency_key = exception_request_id:version`.
- Integration stores operation result hash (`PR#`, file path, commit SHA).
- Duplicate requests return existing correlation object, no new PR.
- GitHub file path deterministic: `exceptions/<year>/<exception_record_id>.yaml`.

---

## Approval and synchronization model

## Decision on pattern
**Recommended: option 4 (Issue + PR) with PR as enforcement artifact.**

- ServiceNow remains master workflow; integration creates:
  1. a GitHub Issue in `exception-registry` for discussion/audit threading,
  2. a GitHub PR containing the machine-readable YAML record.
- Enforcement only recognizes merged PR contents on default branch.

Why this is best:
- Strongest change control (branch protection + CODEOWNERS + checks).
- Excellent auditability (discussion thread + explicit artifact diff).
- Clear operational traceability back to SN request.
- Avoids anti-pattern of direct default branch writes.

## Approver identity preservation
- ServiceNow approver identities + decision timestamps are copied into YAML `spec.approvals[]`.
- PR body includes normalized approval table.
- Optional signed `approval-pack.json` stored in immutable evidence store; pointer written to YAML.

## Sample generated PR body

```markdown
Title: [Exception] EXR-2026-000184 for ASSET-REPO-org-cloud-networking-iac

Source: ServiceNow SN-EXC-0009123 (workflow SNWF-2f9f1c2d-77f5-4fdd-8c67-3f4fb05d17f4)

## Requested Exception
- Baseline: BL-CLOUD-FOUNDATIONAL
- Control: CTRL-GH-CODEOWNERS
- Type: temporary_deviation
- Validity: 2026-04-24 to 2026-05-24

## Approvals from ServiceNow
| Role | Approver | Approval ID | Time (UTC) |
|---|---|---|---|
| security-governance | bob@example.com | APR-SEC-00911 | 2026-04-23T10:15:00Z |
| risk-office | carol@example.com | APR-RISK-00442 | 2026-04-23T10:18:00Z |

## Evidence
- ServiceNow record: https://company.service-now.com/x_gov_exception.do?sys_id=abc123
- Approval package hash: sha256:9b7...42f

## Controls
- [ ] schema/validate passed
- [ ] policy/simulate-impact passed
- [ ] CODEOWNERS approvals complete
```

---

## Enforcement architecture

1. `policy-engine` reads **only merged records** in `exception-registry` default branch.
2. During baseline evaluation, failed controls query active exceptions by:
   - `asset_id`, `baseline_id/control_id`, `valid_from <= now <= valid_until`, `lifecycle_state=active`.
3. Expiry behavior:
   - past `valid_until` -> no waiver; check fails or warns based on control enforcement mode.
4. Revocation behavior:
   - revocation commit/PR sets `lifecycle_state=revoked` immediately; checks stop honoring.
5. Sync delay behavior:
   - if SN says approved but GitHub missing merged record -> policy remains non-waived.
   - merge/deploy gates fail closed for hard controls, warn for advisory controls.

---

## ServiceNow workflow design guidance

## Recommended stages
1. Draft/New
2. Intake validation
3. Triage
4. Risk assessment
5. Compensating control review
6. Approval routing (tiered)
7. Approved - Pending GitHub
8. Active (after GitHub merge callback)
9. Renewal due
10. Expired / Revoked
11. Closed

## Required fields
- `exception_request_id`, `workflow_instance_id`
- `asset_id`, `baseline_id`, `control_id`
- `exception_type`, `business_justification`, `risk_statement`
- `requested_valid_from`, `requested_valid_until`
- `compensating_controls[]`
- `requester`, `owner_group`, `risk_rating`

## Validation rules
- Asset/control/baseline IDs must exist in GitHub catalogs.
- `requested_valid_until` must be <= max policy window from GitHub control policy.
- All exceptions must be time-bound.
- Duplicate active exception detection by `(asset_id, control_id, overlap window)`.

## Routing inputs
- Asset criticality/data classification.
- Control criticality category.
- Business unit, regulatory scope, exception type, risk rating.

## Approval tiers
- Tier 1: Domain owner.
- Tier 2: Security governance.
- Tier 3: Risk/compliance (mandatory for high criticality/regulatory scope).
- Tier 4: Legal/vendor office when third-party obligations apply.

## Renewal rules
- Renewal opens new workflow and creates **new versioned GitHub record** linked to prior `exception_record_id`.
- Max renewals enforced by GitHub policy artifact.

## Closure rules
- Auto-close when GitHub marks `expired` and no renewal in grace period.
- Manual close allowed only with reason code + approver for revoked cases.

## Configurable vs fixed
- Configurable in SN: queues, SLAs, notifications, approval routing policies.
- Fixed by GitHub artifacts: allowed controls, max validity, max renewals, enforcement mode.

---

## Security architecture

- **GitHub App permissions** (least privilege):
  - `Contents: Read/Write` only on governance repos requiring record updates.
  - `Pull requests: Read/Write`, `Issues: Read/Write`, `Checks: Read`.
  - `Metadata: Read` across governed orgs.
- **ServiceNow integration principal**:
  - dedicated technical user with API-only role, no interactive approvals.
- **Token handling**:
  - GitHub App private key in vault/KMS; short-lived installation tokens only.
  - ServiceNow outbound auth via mTLS + OAuth client credentials.
- **OIDC**:
  - GitHub Actions uses OIDC for evidence-store writes (no long-lived cloud creds).
- **Separation of duties**:
  - Request/approve in SN separated from merge authority in GitHub CODEOWNERS.
- **Tamper resistance**:
  - Branch protection forbids direct pushes to default branch.
  - Bot cannot bypass required checks/reviews.
  - Signed commits/tags where feasible.

---

## Audit and evidence design

Preserve and link all of:
- requester identity,
- approver identity + timestamps,
- rationale/risk statement,
- compensating controls,
- attachments/evidence references,
- full change history.

Recommended storage pattern:
- Attachments remain in ServiceNow or enterprise evidence store.
- Integration generates immutable evidence package (JSON + hash) in WORM store.
- GitHub YAML stores **pointers + hashes**, not heavy binaries.
- Long-term retention: external immutable archive (7+ years per policy).

---

## Reporting model

### Combined dashboards
- Exception volume by control, baseline, asset class.
- Active vs expired vs revoked exceptions.
- Approval lead time (SN workflow metric).
- PR merge lead time (GitHub metric).
- Renewal rate and renewal rejection rate.
- Reconciliation failures and mean time to repair.

### Data sources
- GitHub: exception files, PR/check events, policy outcomes.
- ServiceNow: task/approval timelines, assignment/SLA metrics.
- Integration: sync outcomes, retries, dead-letter queue counts.

---

## Failure modes and edge cases

| Scenario | Expected behavior | Auto-remediation | Human path |
|---|---|---|---|
| SN approved but GitHub PR creation fails | SN remains `Approved - Pending GitHub` (not active) | retry with exponential backoff; alert after N failures | platform ops can trigger manual re-sync |
| GitHub merged but SN update fails | Exception active in GitHub; SN stale | webhook retry + reconciliation repairs SN | SN ops manually patch record |
| GitHub expired while SN active | Enforcement treats as expired immediately | reconciliation sets SN to expired | governance reviewer confirms closure |
| Asset metadata mismatch | PR check fails (`asset_id` unresolved) | return validation error to SN | requester corrects asset in SN |
| Duplicate request | idempotency returns existing correlation | no-op | merge duplicate into original ticket |
| Revoked approval after merge | create revocation PR immediately | high-priority sync flow | emergency CAB oversight |
| Emergency exception | fast-track SN path with post-approval evidence deadline | temporary short TTL (e.g., 72h) enforced in GitHub | mandatory retrospective within 5 business days |

---

## Sample webhook/API interaction sequence

1. `ServiceNow -> Integration` `POST /exceptions/sync` (`SN-EXC-0009123:v3`, state `approved_pending_github`).
2. `Integration -> GitHub App API` create branch `exc/SN-EXC-0009123-v3`.
3. `Integration -> GitHub Contents API` add `exceptions/2026/EXR-2026-000184.yaml`.
4. `Integration -> GitHub Pulls API` open PR.
5. `Integration -> ServiceNow API` patch request with PR URL + state `awaiting_github_merge`.
6. `GitHub -> Integration webhook` `pull_request.closed` merged=true.
7. `Integration -> ServiceNow API` patch state `active`, set merge SHA/time.
8. `GitHub Action (expiry)` later marks record expired via PR/commit.
9. `GitHub -> Integration webhook` expired update event.
10. `Integration -> ServiceNow API` patch state `expired` and close tasks.

---

## Sample reconciliation job

**Job:** `exception_sync_reconciler` (hourly incremental, daily full scan)

- Input A: ServiceNow requests in states `approved_pending_github`, `awaiting_github_merge`, `active`, `renewal_due`.
- Input B: GitHub exception records + open PRs + merged states.
- Checks:
  1. Approved in SN with no PR after 15 min.
  2. PR merged in GitHub but SN not `active` after 5 min.
  3. GitHub expired/revoked while SN still active.
  4. Field drift on `valid_until`, `control_id`, `asset_id`.
- Outputs:
  - auto-heal API patches,
  - retry queue entries,
  - incident ticket on repeated failures,
  - daily reconciliation report to governance ops.

---

## Sample state mapping table (canonical)

| ServiceNow state | GitHub state | Enforcement effective? | Notes |
|---|---|---|---|
| `new` | none | No | Intake only |
| `triaged` | none | No | In review |
| `awaiting_approval` | `draft` (optional) | No | Pre-authorization |
| `approved_pending_github` | `submitted` (PR open) | No | Critical anti-split-brain gate |
| `awaiting_github_merge` | `submitted` | No | Checks/reviews running |
| `implemented_active` | `active` | Yes | Only after merge + effective date |
| `renewal_due` | `active` | Yes (until expiry) | Renewal window |
| `expired` | `expired` | No | Waiver removed |
| `revoked` | `revoked` | No | Immediate removal |
| `closed` | `expired` or `revoked` | No | Terminal workflow state |

---

## Rollout plan

1. **Pilot (0-45 days)**
   - One domain + 2 control families.
   - ServiceNow workflow MVP with `approved_pending_github` gating.
   - GitHub App creates Issue+PR in `exception-registry`.
2. **Dual-write/parallel validation (45-90 days)**
   - Continue legacy process in shadow mode.
   - Compare SN-only approvals vs GitHub-enforced outcomes.
   - Track reconciliation drift and fix contracts.
3. **Cutover (90-120 days)**
   - Disable legacy activation paths.
   - Enforcement consumes only GitHub records.
   - SN dashboards updated to reflect GitHub effective state.
4. **Enterprise rollout (120+ days)**
   - Expand to infra/cloud/SaaS/endpoints/vendor/legal domains.
   - Regionalization, data residency controls, multi-instance SN support.

---

## Anti-patterns (do not do)

- Treating `ServiceNow Approved` as active without GitHub merge.
- Direct bot commits to default branch bypassing PR checks.
- Storing large evidence binaries in Git repos.
- Allowing renewals by silently extending `valid_until` without new version/audit event.
- Separate manual status edits in both systems without reconciliation.

---

## Recommended Target Pattern

Use **ServiceNow-driven workflow + GitHub Issue+PR codification** with a strict activation gate:

1. SN approval transitions to `approved_pending_github`.
2. Integration creates GitHub Issue+PR with versioned exception YAML.
3. GitHub checks + CODEOWNERS approvals + merge make it enforceable.
4. Policy engine honors only merged active records.
5. Reconciliation ensures bi-directional state convergence.

This yields strongest auditability, least privilege, and no split-brain ownership.

## Minimum Viable Integration in 30 Days

- ServiceNow form with required IDs and approvals.
- Integration endpoint with idempotency and PR creation only.
- GitHub Action validators for exception schema and date bounds.
- Webhook callback to set SN state to active only on merge.
- Hourly reconciler for two failure modes (missing PR, missing SN update).

## Future Enhancements

- Cryptographic signing of approval bundles and in-repo attestations.
- Automated compensating-control evidence verification hooks.
- Risk-adaptive routing using asset criticality + threat intel.
- Self-service renewal wizard with policy-guarded bounds.
- Federated reporting lakehouse for cross-tool governance analytics.
