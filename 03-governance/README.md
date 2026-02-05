# Governance & Audit

This module demonstrates governance, RBAC, and audit logging for ML deployments.

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

## Hands-On Exercises

1. **Exercise 1**: Set up RBAC roles for MLOps team
2. **Exercise 2**: Configure diagnostic settings for audit logs
3. **Exercise 3**: Query audit logs with Log Analytics (KQL)
4. **Exercise 4**: Create governance dashboard in Power BI
