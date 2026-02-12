# Governance & Audit

This module generates compliance reports showing model inventory, deployment events, and audit trails from Azure Activity Log. Outputs both JSON and an interactive HTML report.

## What It Does

1. **`audit_logging.py`** — Core library that:
   - Queries Azure Activity Log for deployment & model registration events
   - Inventories all registered models (name, version, tags)
   - Lists active endpoints and their provisioning state
   - Supports model registration with governance metadata (author, approver, data version, compliance tags)

2. **`run_audit_report.py`** — Runner script that calls `audit_logging.py` and outputs:
   - `audit_report.json` — machine-readable audit data
   - `Governance_Report.html` — interactive HTML report (auto-generated)

3. **`generate_html_report.py`** — Converts audit JSON into a standalone `Governance_Report.html` with:
   - Summary cards (model count, endpoint count, event counts)
   - Model registry inventory table
   - Active endpoints with status badges
   - Deployment and registration audit trails
   - Compliance notes

## Quick Start

```powershell
# Set env vars
$env:AZURE_SUBSCRIPTION_ID = "<your-sub>"
$env:AZURE_RESOURCE_GROUP = "rg-dnd-mlops-demo"
$env:AZURE_ML_WORKSPACE = "mlw-dndmlops2-dev"

# Generate the report (JSON + HTML)
python .\03-governance\run_audit_report.py

# Open the HTML report
start .\03-governance\Governance_Report.html
```

## Key Governance Questions Answered

| Question | Azure Solution |
|----------|---------------|
| Who deployed what? | Azure Activity Log + Model Registry |
| When was it deployed? | Model Registry timestamps + Azure Monitor |
| Why was it deployed? | Model tags, descriptions, and run lineage |
| What data was used? | Data lineage in Azure ML |
| What code was used? | Git integration + Environment snapshots |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Governance Stack                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Azure ML Workspace                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │   │
│  │  │ Model       │  │ Environment │  │ Data Assets         │ │   │
│  │  │ Registry    │  │ Registry    │  │ (with lineage)      │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Audit & Compliance                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │   │
│  │  │ Activity    │  │ Azure       │  │ Azure Policy        │ │   │
│  │  │ Logs        │  │ RBAC        │  │ (Compliance)        │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Export & Reporting                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │   │
│  │  │ Log         │  │ Azure       │  │ Power BI            │ │   │
│  │  │ Analytics   │  │ Sentinel    │  │ Dashboards          │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Azure RBAC Roles for MLOps

| Role | Permissions |
|------|-------------|
| **AzureML Data Scientist** | Run experiments, register models |
| **AzureML Compute Operator** | Start/stop compute |
| **AzureML Registry User** | Read models from registry |
| **Contributor** | Full access except RBAC |
| **Reader** | Read-only access |

## Recommended Custom Roles

### MLOps Engineer
```json
{
  "Name": "MLOps Engineer",
  "Description": "Can deploy and manage ML endpoints",
  "Actions": [
    "Microsoft.MachineLearningServices/workspaces/endpoints/*",
    "Microsoft.MachineLearningServices/workspaces/models/read",
    "Microsoft.MachineLearningServices/workspaces/environments/read"
  ],
  "NotActions": [],
  "AssignableScopes": ["/subscriptions/{subscription-id}"]
}
```

### Model Reviewer
```json
{
  "Name": "Model Reviewer",
  "Description": "Can view and approve models for deployment",
  "Actions": [
    "Microsoft.MachineLearningServices/workspaces/models/read",
    "Microsoft.MachineLearningServices/workspaces/experiments/read",
    "Microsoft.MachineLearningServices/workspaces/jobs/read"
  ],
  "NotActions": [],
  "AssignableScopes": ["/subscriptions/{subscription-id}"]
}
```

## Model Registry Best Practices

### Required Model Tags
```python
model = Model(
    path="./model",
    name="classification-model",
    description="Document classification model for Pro A/B",
    tags={
        "author": "data-science-team",
        "use_case": "document_classification",
        "data_version": "v2.1",
        "training_date": "2026-01-15",
        "approved_by": "mlops-lead",
        "approval_date": "2026-01-16",
    },
    properties={
        "accuracy": "0.94",
        "f1_score": "0.92",
        "training_job_id": "job-12345",
    }
)
```

## Hands-On Steps

1. Run `python .\03-governance\run_audit_report.py` to generate the audit report
2. Open `Governance_Report.html` in a browser and review the model inventory
3. Check deployment and registration audit trails for WHO/WHAT/WHEN
4. Review compliance notes and RBAC guidance
