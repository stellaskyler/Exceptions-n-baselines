# GitHub Enterprise Reference Architecture for Baseline & Exception Management

## 1) Executive Summary: Target Operating Model

The enterprise uses **GitHub Enterprise Cloud as the governance plane** and system of record for:
- baseline definitions (controls, policies, standards, required practices),
- exception records (waivers, risk acceptances, compensating controls, temporary deviations),
- approval decisions and audit history,
- evidence pointers and enforcement outcomes.

The operating model is **policy-as-code + records-as-code**:
- All governance artifacts live in versioned repositories.
- All changes are pull requests with strict review and branch protections.
- Approvals are codified through CODEOWNERS, protected branches, and required checks.
- A policy evaluation service (GitHub App + Actions) continuously resolves baseline applicability, evaluates exception validity, and emits enforcement decisions to GitHub checks and external enforcement systems.

GitHub is the source of truth for governance state and traceability; external tools remain execution engines for domain-specific controls (cloud policy engines, endpoint tools, ticketing, SIEM, GRC reporting).

---

## 2) Reference Architecture

### 2.1 Enterprise / Account Structure

- **GitHub Enterprise Account (single)**
  - Enforced SAML SSO and SCIM provisioning.
  - Enterprise-managed users/groups synced from IdP.
  - Enterprise audit log export enabled.
- **Governance Org (`org-governance`)**
  - Owns governance repositories and central automation.
  - Restricted admin model; break-glass owners are minimal.
- **Domain Orgs** (examples)
  - `org-eng`, `org-security`, `org-it`, `org-cloud`, `org-vendor`, `org-legal`.
  - Product/service repos and domain-specific assets.

### 2.2 ASCII Architecture Diagram

```text
                    +--------------------------------------+
                    | GitHub Enterprise Cloud              |
                    | (SSO/SCIM, audit log, org policies) |
                    +------------------+-------------------+
                                       |
                 +---------------------+---------------------+
                 |                                           |
      +----------v-----------+                   +-----------v-----------+
      | org-governance       |                   | Domain Orgs           |
      |----------------------|                   | (eng/sec/it/cloud...) |
      | baseline-catalog     |<-----PR/Checks----| product repos         |
      | exception-registry   |                   | infra repos           |
      | asset-register       |<--metadata sync-->| non-repo asset links  |
      | policy-engine        |-----status------->| required checks       |
      | template-factory     |-----bootstrap---->| new repos             |
      | governance-docs      |                   |                       |
      +----------+-----------+                   +-----------+-----------+
                 |                                           |
                 | Webhooks / GraphQL / REST                | OIDC tokens
                 v                                           v
      +----------+------------------------+      +-----------+------------------+
      | Governance GitHub App             |      | External systems             |
      | - applicability resolver          |      | Cloud/SaaS/ITSM/SIEM/GRC     |
      | - exception state evaluator       |      | - execute controls           |
      | - check-run publisher             |      | - provide evidence pointers  |
      +----------------+------------------+      +------------------------------+
                       |
                       v
            +----------+-------------+
            | Evidence Lake (WORM)   |
            | immutable retention    |
            +------------------------+
```

### 2.3 Required Repositories (Governance Org)

1. **`baseline-catalog`**
   - Versioned baseline and control definitions.
   - Applicability logic and rollout rings.
2. **`exception-registry`**
   - Machine-readable exception records and lifecycle state.
   - Renewal/expiry workflow definitions.
3. **`policy-engine`**
   - Resolver + evaluator code.
   - Reusable Actions workflows and policy decision logic.
4. **`asset-register`**
   - Records for governed assets (repo and non-repo).
   - Ownership, criticality, data classification, environment.
5. **`template-factory`**
   - Repository templates, starter workflows, CODEOWNERS scaffolding.
6. **`governance-docs`**
   - Human-readable standards, process docs, control narratives.

---

## 3) Representation Model

### 3.1 How governed objects are represented

- **Repositories**: represented as GitHub repos + custom properties + corresponding asset record in `asset-register`.
- **Non-repo assets** (SaaS tenants, vendors, endpoint fleets, cloud accounts, business processes): represented as YAML records in `asset-register` with unique immutable `asset_id` and external system pointers.
- **Baselines**: YAML files in `baseline-catalog/baselines/` referencing one or more controls.
- **Controls**: YAML files in `baseline-catalog/controls/` with test method and enforcement mode.
- **Exceptions**: YAML records in `exception-registry/exceptions/` with bounded validity and compensating controls.

### 3.2 Metadata flow

1. Asset owner submits/updates asset record via PR.
2. Policy engine enriches with GitHub metadata (repo visibility, branch protections, Actions settings).
3. Applicability resolver maps asset attributes to applicable baselines.
4. Evaluator computes control compliance minus active exceptions.
5. Decision artifacts are posted as:
   - GitHub check runs (for gating),
   - commit statuses,
   - signed decision JSON in evidence storage,
   - pointers written back to issue/PR comments.

### 3.3 Approval and enforcement flow

- Baseline/exception changes require PR approvals from defined CODEOWNERS groups.
- Required checks include schema validation, policy simulation, and impact analysis.
- Merges to protected branch trigger rollout workflows.
- Domain repositories consume latest approved baseline bundle as a versioned release.
- Merge/deploy in domain repos is blocked if required policy checks fail and no valid exception exists.

---

## 4) Recommended Repository Topology

```text
org-governance/
  baseline-catalog/
    baselines/
    controls/
    schemas/
    rollout-rings/
    changelogs/
  exception-registry/
    exceptions/
    schemas/
    issue-forms/
    lifecycle-events/
  policy-engine/
    app/
    workflows/
    libraries/
    contracts/
  asset-register/
    assets/
      repo/
      cloud-account/
      saas/
      endpoint-fleet/
      vendor/
      process/
    schemas/
  template-factory/
    repo-templates/
    reusable-workflows/
    starter-policies/
  governance-docs/
    standards/
    raci/
    control-objectives/
    auditor-guides/
```

---

## 5) Canonical Data Model

### 5.1 Baseline Definition

Required fields:
- `baseline_id` (immutable)
- `name`, `version`, `status` (`draft|approved|deprecated`)
- `scope` (asset selectors)
- `controls[]` (control IDs + requiredness)
- `rollout` (ring + effective dates)
- `approvals` (required roles)
- `evidence_requirements`

### 5.2 Control Definition

Required fields:
- `control_id`, `objective`, `rationale`
- `test_method` (`github_native|action|app|external`)
- `enforcement_mode` (`advisory|soft_fail|hard_fail`)
- `implementation` (query/check contract)
- `evidence_contract` (what proof must exist)

### 5.3 Asset Record

Required fields:
- `asset_id`, `asset_type`, `system_of_record_ref`
- `owner`, `business_unit`, `criticality`, `data_classification`
- `environment` (`prod|staging|dev`)
- `github` block if repo-backed
- `tags` for applicability

### 5.4 Exception Record

Required fields:
- `exception_id`, `asset_id`, `baseline_id` and/or `control_ids`
- `exception_type` (`waiver|risk_acceptance|compensating_control|temporary_deviation`)
- `justification`, `risk_statement`
- `compensating_controls[]`
- `requested_by`, `approvers[]`
- `state` (`draft|submitted|approved|active|expired|revoked|rejected`)
- `valid_from`, `valid_until`, `max_renewals`
- `renewal_history[]`, `revocation`
- `evidence_links[]`

### 5.5 Approval / Renewal / Expiry State Machine

```text
draft -> submitted -> approved -> active -> expired
                        |            |
                        |            +-> revoked
                        +-> rejected

expired -> renewal_requested -> approved -> active
```

Rules:
- `valid_until` mandatory.
- Expired exceptions are ignored by evaluator.
- Renewal creates new decision event with incremented renewal count.
- Revocation is immediate and blocks merges/deploys where exception was relied upon.

---

## 6) Example Schemas and YAML

### 6.1 Baseline Schema (JSON Schema excerpt)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Baseline",
  "type": "object",
  "required": ["baseline_id", "name", "version", "status", "scope", "controls"],
  "properties": {
    "baseline_id": {"type": "string", "pattern": "^BL-[A-Z0-9_-]+$"},
    "name": {"type": "string"},
    "version": {"type": "string"},
    "status": {"enum": ["draft", "approved", "deprecated"]},
    "scope": {
      "type": "object",
      "required": ["asset_types"],
      "properties": {
        "asset_types": {"type": "array", "items": {"type": "string"}},
        "tags_all": {"type": "array", "items": {"type": "string"}},
        "env_in": {"type": "array", "items": {"type": "string"}}
      }
    },
    "controls": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["control_id", "required"],
        "properties": {
          "control_id": {"type": "string"},
          "required": {"type": "boolean"}
        }
      }
    }
  }
}
```

### 6.2 Exception Schema (JSON Schema excerpt)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Exception",
  "type": "object",
  "required": [
    "exception_id","asset_id","exception_type","state","valid_from","valid_until","justification"
  ],
  "properties": {
    "exception_id": {"type": "string", "pattern": "^EX-[0-9]{6}$"},
    "asset_id": {"type": "string"},
    "baseline_id": {"type": "string"},
    "control_ids": {"type": "array", "items": {"type": "string"}},
    "exception_type": {"enum": ["waiver","risk_acceptance","compensating_control","temporary_deviation"]},
    "state": {"enum": ["draft","submitted","approved","active","expired","revoked","rejected"]},
    "valid_from": {"type": "string", "format": "date"},
    "valid_until": {"type": "string", "format": "date"},
    "max_renewals": {"type": "integer", "minimum": 0},
    "justification": {"type": "string", "minLength": 20},
    "risk_statement": {"type": "string"},
    "compensating_controls": {"type": "array", "items": {"type": "string"}}
  }
}
```

### 6.3 Example Baseline YAML

```yaml
baseline_id: BL-CLOUD-FOUNDATIONAL
name: Cloud Foundational Security Baseline
version: 1.3.0
status: approved
scope:
  asset_types: [cloud-account, repo]
  tags_all: [regulated, internet-facing]
  env_in: [prod]
controls:
  - control_id: CTRL-GH-BRANCH-PROTECT
    required: true
  - control_id: CTRL-GH-CODEOWNERS
    required: true
  - control_id: CTRL-CLOUD-CIS-LOGGING
    required: true
rollout:
  ring: ring-1
  effective_from: 2026-06-01
approvals:
  required_roles: [platform-governance, security-governance]
evidence_requirements:
  - check_run: policy/baseline-eval
  - external_attestation: cloud-posture-snapshot
```

### 6.4 Example Exception YAML

```yaml
exception_id: EX-004219
asset_id: ASSET-REPO-org-cloud-networking-iac
baseline_id: BL-CLOUD-FOUNDATIONAL
control_ids: [CTRL-GH-CODEOWNERS]
exception_type: temporary_deviation
state: active
requested_by: user:alice@example.com
approvers:
  - role: platform-governance
    approver: user:bob@example.com
    decision: approved
    decided_at: 2026-04-10T18:25:00Z
justification: >-
  Team is migrating monorepo ownership model; temporary CODEOWNERS mismatch
  expected for 14 days while service boundaries are split.
risk_statement: Unauthorized review bypass risk is mitigated by mandatory security reviewer assignment in PR template.
compensating_controls:
  - CTRL-PR-SECURITY-REVIEW-MANDATORY
valid_from: 2026-04-10
valid_until: 2026-04-24
max_renewals: 1
renewal_history: []
evidence_links:
  - type: pr
    url: https://github.com/org-cloud/networking-iac/pull/982
```

### 6.5 Example Non-repo Asset YAML

```yaml
asset_id: ASSET-SAAS-workday-prod
asset_type: saas
name: Workday Production Tenant
system_of_record_ref:
  system: vendor-inventory
  external_id: VND-00231
owner:
  team_slug: hr-platform
  manager_upn: manager@example.com
business_unit: HR
criticality: high
data_classification: restricted
environment: prod
tags: [pii, sox, regulated]
integrations:
  - type: scim
    provider: okta
  - type: siem
    provider: splunk
evidence_sources:
  - type: soc2_report
    url: https://evidence.example.com/workday/soc2-2026.pdf
```

---

## 7) GitHub-Native Governance Model

### 7.1 Custom Properties (native)

Define enterprise/repo custom properties (examples):
- `asset_id`
- `data_classification` (`public|internal|confidential|restricted`)
- `criticality` (`low|medium|high|mission_critical`)
- `regulatory_scope` (`none|sox|hipaa|pci|multi`)
- `baseline_ring` (`ring-0|ring-1|ring-2`)
- `exception_required` (`true|false`)

Use in ruleset targeting and policy resolver input.

### 7.2 Rulesets + Branch protection (native)

- Enterprise rulesets for default protections:
  - Require PRs for default branch.
  - Require status checks: `policy/baseline-eval`, `policy/exception-eval`.
  - Require signed commits/tags where applicable.
  - Restrict force push and branch deletion.
- Repo-level protected branch overlays for stricter domains.

### 7.3 CODEOWNERS (native)

- Governance repos:
  - `baseline-catalog`: Platform Governance + Security Governance owners.
  - `exception-registry`: Risk Office + Domain Security owners.
- Domain repos:
  - Required domain owner + security owner review for policy-impacting paths.

### 7.4 Required checks (Actions + App)

- `schema/validate` (Action)
- `policy/simulate-impact` (Action)
- `policy/baseline-eval` (GitHub App check run)
- `policy/exception-eval` (GitHub App check run)

### 7.5 Reusable workflows (Actions)

- Central reusable workflows in `policy-engine/.github/workflows`:
  - `validate-governance-record.yml`
  - `evaluate-policy.yml`
  - `expire-exceptions.yml`
  - `publish-evidence.yml`

Domain repos call via `workflow_call`, pinned to release tags/SHA.

### 7.6 Issue types/forms + Projects (native)

- `exception-registry` issue forms:
  - New exception request
  - Renewal request
  - Revocation request
- Project fields:
  - `Exception State`, `Asset ID`, `Baseline ID`, `Expiry Date`, `Risk Level`, `Approver`.
- Views:
  - `Expiring in 7 days`
  - `Active high-risk exceptions`
  - `Awaiting approval`

Issue submission triggers workflow that creates/updates exception YAML via bot PR.

---

## 8) Policy Enforcement Design

### 8.1 Baseline applicability resolution

Resolution algorithm (policy-engine App):
1. Load asset record by `asset_id`.
2. Match baseline `scope` selectors against asset attributes and repo custom properties.
3. Filter by rollout ring/date.
4. Produce ordered list of applicable controls.

Output contract (JSON):
- `asset_id`
- `applicable_baselines[]`
- `required_controls[]`
- `decision_timestamp`

### 8.2 Exception evaluation

For each failed required control:
1. Query active exceptions where `asset_id` matches and control/baseline scope includes the failure.
2. Validate exception state = `active` and current date <= `valid_until`.
3. Verify compensating control evidence (if declared).
4. Return `waived` or `enforce`.

### 8.3 Expiry enforcement

- Scheduled workflow (`cron` hourly/daily) scans exception records.
- Transitions expired records to `expired` via bot PR or direct API write with signed bot commit.
- Posts notifications (issue comment + Slack/Teams webhook external integration).
- Immediately updates evaluator cache; subsequent merges fail if exception was required.

### 8.4 Merge / deploy gates

- **Merge gate**: required check on PR must be `success` only if all required controls pass or valid exception exists.
- **Deploy gate**: environment protection rule requires successful `policy/deploy-eval` check on release artifact commit/tag.

### 8.5 Evidence generation and storage

- GitHub artifacts:
  - check logs,
  - SARIF/JSON reports,
  - PR review history,
  - signed commits and tags.
- External immutable evidence lake (required):
  - write-once object storage with retention lock.
  - store decision JSON, hash of source commit, timestamp, signer identity.
- Record only evidence pointers/hashes in GitHub to avoid bloating repos.

---

## 9) Security Architecture

### 9.1 Identity and admin boundaries

- SSO enforced; no unmanaged personal accounts.
- SCIM group-to-team mapping for least privilege.
- Separate admin teams:
  - Enterprise platform admins,
  - governance maintainers,
  - domain maintainers.
- Break-glass accounts monitored and excluded from normal automation tokens.

### 9.2 Bot/App permissions

- Governance GitHub App with fine-grained permissions:
  - Read metadata across orgs.
  - Checks write on participating repos.
  - Contents write only on governance repos where bot updates records.
- No classic PATs.

### 9.3 OIDC vs stored secrets

- Prefer OIDC federation from Actions to cloud providers/evidence storage.
- Store zero long-lived cloud credentials in GitHub.
- If unavoidable, org/environment secrets with strict repository allow-lists and rotation policy.

### 9.4 Workflow trust boundaries

- Untrusted code (PR from forks) cannot access privileged tokens.
- Split workflows:
  - `pull_request` for lint/validate only.
  - `workflow_run` or `pull_request_target` with hardened controls for privileged operations.
- Pin third-party actions by commit SHA.

### 9.5 Audit log export + long-term retention

- Enterprise audit log streamed to SIEM (external integration).
- Retain governance decision records and approvals for compliance period (e.g., 7 years) in immutable archive.
- Regular reconciliation job compares GitHub state and evidence lake hashes.

---

## 10) Rollout Plan

### Phase 1: Pilot (0-30 days)
- Stand up `org-governance` and 6 core repos.
- Implement baseline + exception schemas and validation workflow.
- Onboard 10–20 pilot repos across 2 domains.
- Enable required policy checks in advisory mode first, then hard-fail for one baseline.

### Phase 2: Platform Hardening (30-90 days)
- Deploy GitHub App evaluator with caching and signed decisions.
- Add expiry daemon workflow and Project dashboards.
- Add OIDC-based evidence publishing to immutable storage.
- Conduct red-team style abuse-case testing of workflow permissions.

### Phase 3: Domain Onboarding (90-180 days)
- Template-driven onboarding waves by domain.
- Bulk assign repo custom properties via script + API.
- Migrate existing exceptions from spreadsheets/tickets into `exception-registry`.
- Define domain SLAs for exception review and renewal.

### Phase 4: Enterprise Scale-out (180+ days)
- Expand to non-repo assets (vendors, SaaS, endpoints, processes).
- Add integration adapters for cloud posture tools, endpoint platforms, vendor systems.
- Add executive and audit reporting views fed from decision artifacts.

---

## 11) Risks, Tradeoffs, and Anti-Patterns

### Where GitHub is a good fit
- Versioned governance definitions.
- Approval trails and policy change control.
- Repo and engineering-facing control enforcement.
- Developer-friendly automation and transparency.

### Where GitHub should not be stretched
- Full CMDB replacement (asset discovery at enterprise scale should remain in dedicated tooling).
- Ticketing/ERP workflow replacement.
- Long-term high-volume evidence warehouse.
- Real-time endpoint or network control execution plane.

### Must live outside GitHub
- Authoritative identity provider.
- Immutable long-term archival store.
- Certain enforcement systems (cloud SCP engines, MDM, CASB, SIEM correlation).
- Financial/legal systems of record.

Anti-patterns:
- Free-form exception text with no schema/expiry.
- “Permanent temporary” exceptions (no max renewal).
- Using repo admins to bypass required checks without dual control.
- Keeping policy evaluator logic only in workflow YAML without testable code.

---

## 12) Native vs Extension Capability Matrix

| Capability | Native GitHub | Actions / reusable workflow | GitHub App / bot | External integration |
|---|---|---|---|---|
| PR approvals, CODEOWNERS, branch protections | ✅ |  |  |  |
| Ruleset targeting by custom properties | ✅ |  |  |  |
| Schema validation on governance records |  | ✅ |  |  |
| Baseline applicability computation across orgs |  |  | ✅ |  |
| Exception lifecycle automation |  | ✅ | ✅ |  |
| Cross-repo status checks at scale |  |  | ✅ |  |
| Evidence packaging |  | ✅ | ✅ | ✅ (immutable store) |
| Cloud/endpoint/vendor control execution |  |  |  | ✅ |
| Enterprise reporting for auditors |  | ✅ | ✅ | ✅ |

---

## 13) Sample Approval Workflow (Exception)

1. Requester submits exception via issue form in `exception-registry`.
2. Workflow generates `exceptions/EX-xxxxxx.yaml` in PR.
3. Required checks run:
   - schema validation,
   - duplicate detection,
   - policy impact simulation.
4. CODEOWNERS required approvals:
   - Domain owner,
   - Security governance,
   - Risk/compliance (for high criticality).
5. Merge to protected branch sets state to `approved` then `active` on `valid_from`.
6. Evaluator recognizes active exception and can waive specific failed controls.
7. Before `valid_until`, renewal issue is auto-created; no action => auto-expire.

---

## 14) Sample Policy Evaluation Workflow

**Trigger**: Pull request in any governed repo.

1. Reusable workflow `evaluate-policy.yml` starts.
2. Collect context:
   - repo custom properties,
   - linked `asset_id`,
   - changed files/paths,
   - target environment.
3. Call policy-engine App API:
   - `POST /evaluate` with `{asset_id, commit_sha, changed_paths}`.
4. App resolves applicable baselines and evaluates required controls.
5. App checks exception registry for active, in-scope exceptions.
6. App returns decision payload:
   - pass/fail per control,
   - exception references,
   - expiry warnings.
7. Workflow publishes:
   - GitHub check run summary,
   - JSON artifact,
   - optional SARIF.
8. Required status check gate enforces merge outcome.

---

## 15) Minimum Viable Implementation (30 Days)

The smallest credible implementation:

### Scope
- Govern **repository assets only** in two pilot orgs.
- Enforce **3 controls**:
  1. default branch PR required,
  2. CODEOWNERS present,
  3. at least one required security check.
- Support **temporary deviation exceptions** with max 30-day validity.

### Deliverables
1. Governance org with repositories:
   - `baseline-catalog`, `exception-registry`, `policy-engine`, `asset-register`, `template-factory`, `governance-docs`.
2. JSON Schemas + YAML records for baseline/exception/asset.
3. Reusable workflows:
   - record validation,
   - exception expiry scan,
   - policy evaluation (initially Action-based, no external service).
4. Enterprise ruleset requiring `policy/baseline-eval` check on pilot repos.
5. Exception issue form + bot PR generation.
6. Weekly export of decisions and PR metadata to immutable storage (initial script acceptable).

### Acceptance Criteria
- 20 pilot repos onboarded with asset IDs and custom properties.
- 100% governance PRs require CODEOWNERS approval.
- Expired exceptions automatically stop waiving failures within 24h.
- Auditors can trace one control decision from baseline commit -> exception approval -> PR gate outcome -> evidence record.

This MVP is intentionally narrow but production-realistic; it establishes data contracts, approval rigor, and enforcement paths that scale to non-repo assets and broader domains.

---

## Implementation Scaffold (Code)

This repository now includes executable scaffolding for:
- governance schemas and sample records,
- policy evaluation engine modules,
- ServiceNow-to-GitHub integration stubs with idempotency,
- GitHub Actions workflow templates,
- schema/contract/unit/integration tests.

### Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
make all
```
