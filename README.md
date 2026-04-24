# Exceptions & Baselines Reference Implementation

This repository is a working scaffold for governance-as-code using GitHub as the enforcement source of truth, with a ServiceNow workflow integration model for exception intake and approval orchestration.

It includes:
- machine-readable baseline, control, asset, and exception records,
- JSON Schemas and contract tests,
- a lightweight policy evaluation engine,
- a ServiceNow ↔ GitHub integration stub with idempotency and reconciliation checks,
- scripts and Make targets for validation, expiry, evidence publishing, and test execution.

---

## What this repository models

### Core operating model

- **GitHub is the enforcement authority**: baseline/control definitions and exception records in `exception-registry` determine whether an exception is active for policy evaluation.
- **ServiceNow is the workflow authority**: intake, routing, human approvals, and SLA handling occur in ServiceNow.
- **Integration bridges both systems**: ServiceNow approvals authorize codification, but an exception only becomes enforceable after the GitHub record is merged and active by date.

### Repository layout

```text
baseline-catalog/                 # Baseline + control definitions and schemas
asset-register/                   # Asset inventory records and schema
exception-registry/               # Exception records, lifecycle docs, schemas
policy-engine/                    # Evaluator, resolver, contracts, feature flags
integration-servicenow-github/    # Sync/reconciliation stubs + contracts
scripts/                          # Validation, expiry, evidence publishing helpers
tests/                            # Unit, contract, and integration test suites
governance-docs/                  # Standards, runbooks, RACI, acceptance docs
```

---

## Data contracts and records

### Canonical records in this repo

- Baseline schema: `baseline-catalog/schemas/baseline.schema.json`
- Control schema: `baseline-catalog/schemas/control.schema.json`
- Asset schema: `asset-register/schemas/asset.schema.json`
- Exception schema: `exception-registry/schemas/exception.schema.json`
- Approval pack schema: `exception-registry/schemas/approval-pack.schema.json`

### Example records

- Baseline: `baseline-catalog/baselines/BL-CLOUD-FOUNDATIONAL.yaml`
- Controls:
  - `baseline-catalog/controls/CTRL-GH-BRANCH-PROTECT.yaml`
  - `baseline-catalog/controls/CTRL-GH-CODEOWNERS.yaml`
  - `baseline-catalog/controls/CTRL-PR-SECURITY-REVIEW-MANDATORY.yaml`
- Asset: `asset-register/assets/repo/ASSET-REPO-org-cloud-networking-iac.yaml`
- Exception: `exception-registry/exceptions/2026/EXR-2026-000184.yaml`

---

## Policy engine (local module)

`policy-engine/app/main.py` exposes Python-callable entry points:

- `evaluate(request: dict) -> dict`
  - loads asset data,
  - resolves applicable controls from approved baselines,
  - loads active exceptions,
  - returns pass/fail + waived/enforced decisions.
- `simulate_impact(request: dict) -> dict`
  - lightweight simulation stub.

### Example evaluation request shape

```json
{
  "asset_id": "ASSET-REPO-org-cloud-networking-iac",
  "decision_date": "2026-04-24",
  "check_results": {
    "CTRL-GH-BRANCH-PROTECT": true,
    "CTRL-GH-CODEOWNERS": false,
    "CTRL-PR-SECURITY-REVIEW-MANDATORY": true
  }
}
```

Contract examples/schemas are in:
- `policy-engine/contracts/evaluation-request.schema.json`
- `policy-engine/contracts/evaluation-response.schema.json`
- `policy-engine/contracts/examples/`

---

## ServiceNow integration model (combined reference)

This README now supersedes and consolidates the previous standalone ServiceNow integration doc.

### Responsibility boundaries

| Capability | System of record |
|---|---|
| Baseline/control definitions | GitHub (`baseline-catalog`) |
| Enforceable exception state (`active`, `expired`, `revoked`) | GitHub (`exception-registry`) |
| Intake workflow, routing, approvals, SLAs | ServiceNow |
| Correlation/idempotency, retries, reconciliation | Integration service |

### Lifecycle synchronization

High-level lifecycle mapping:

1. ServiceNow request reaches **approved_pending_github**.
2. Integration `sync_exception(...)` creates a deterministic PR in governance GitHub.
3. Validation/review gates pass and PR merges.
4. Exception becomes active based on record state/dates in GitHub.
5. Reconciliation jobs detect and report drift between SN and GitHub.

### Integration implementation in this repo

- Sync route logic: `integration-servicenow-github/sn_app/routes.py`
- Public callable wrappers: `integration-servicenow-github/sn_app/main.py`
- Mock GitHub client behavior: `integration-servicenow-github/sn_app/github_client.py`
- Idempotency store: `integration-servicenow-github/sn_app/idempotency_store.py`
- State mapping config: `integration-servicenow-github/config/state-mapping.yaml`
- Reconciliation checks:
  - `integration-servicenow-github/sn_app/checks/missing_pr.py`
  - `integration-servicenow-github/sn_app/checks/field_drift.py`
  - `integration-servicenow-github/sn_app/checks/stale_sn_status.py`
  - `integration-servicenow-github/sn_app/checks/expired_mismatch.py`

### Contract files

- ServiceNow sync request schema: `integration-servicenow-github/contracts/sn-exception-request.schema.json`
- Sync response schema: `integration-servicenow-github/contracts/sync-response.schema.json`
- Reconciliation report schema: `integration-servicenow-github/reports/reconciliation_report.schema.json`

---

## Local development

### Prerequisites

- Python 3.11+
- `pip`

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Validation + tests

```bash
make validate-schemas
make test-unit
make test-contract
make test-integration
make all
```

`make all` runs schema validation and all test suites.

---

## Governance docs

Supporting process and control documentation is under `governance-docs/`, including:
- rollout and review standards,
- reconciliation runbook,
- RACI,
- MVP and ServiceNow integration acceptance criteria,
- audit evidence chain guidance.

---

## Notes and limitations

- Integration and API components here are scaffolds/stubs intended for contract-first implementation and testing.
- The GitHub client in integration code is mocked by design.
- The evaluator entry points are module functions (not a production HTTP server in this repo).

