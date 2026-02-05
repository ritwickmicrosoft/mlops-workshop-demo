# Workshop Runbook — DND/CAF MLOps Demo (End-to-End)

This runbook is organized in the exact presentation + demo flow:

1. Azure Machine Learning (workspace, pipelines, model registry)
2. Azure Data Factory (pipelines, triggers) — optional provisioning
3. Azure Event Grid (event-driven automation)
4. Azure Monitor (observability dashboards/logs)
5. Application Insights (endpoint monitoring)
6. Azure Key Vault (secrets management)
7. Azure Container Registry (Docker images)
8. Azure ML Feature Store (shared feature management) — optional provisioning

## 0) Prereqs (everyone)

- Azure subscription access (Contributor) to a workshop RG
- `az` CLI installed and logged in: `az login`
- Python 3.9+ and `pip`

### Environment variables (PowerShell)

```powershell
$env:AZURE_SUBSCRIPTION_ID = "<subscription-id>"
$env:AZURE_RESOURCE_GROUP = "rg-dnd-mlops-demo"
$env:AZURE_ML_WORKSPACE = "mlw-dndmlops-dev"
```

### Install repo dependencies

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 1) Azure Machine Learning — MLflow + Registry + Endpoint

### Demo: MLflow tracking to Azure ML + model registration + endpoint

- Run: [notebooks/01_azure_ml_mlflow_quickstart.ipynb](notebooks/01_azure_ml_mlflow_quickstart.ipynb)
- Show in Studio:
  - Experiments → metrics/artifacts
  - Models → registered `spam-classifier`
  - Endpoints → deployed endpoint (if you ran the optional deploy cells)

### Demo: Automated retraining pipeline (Azure ML pipeline)

- Submit pipeline:

```powershell
python .\01-automated-retraining\submit_pipeline.py
```

- Simulate “event-driven data change” (local simulation that still submits to Azure ML):

```powershell
python .\01-automated-retraining\simulate_event_trigger.py
```

## 2) Azure Data Factory — Pipelines + Triggers (optional)

Recommended workshop approach:
- Provision ADF ahead of time, with a pipeline that (a) copies a CSV into the AML storage path OR (b) calls a webhook/Function that triggers retraining.
- During the demo, show:
  - Pipeline run history
  - Trigger firing (schedule/event)

---

## 3) Azure Event Grid — Event-driven automation

In this repo, the reliable workshop demo is:
- Upload/change a dataset (conceptually)
- Run [01-automated-retraining/simulate_event_trigger.py](01-automated-retraining/simulate_event_trigger.py)

If you want a true Event Grid → Function → AML pipeline trigger, we can add that as an optional infra + function app (more moving parts, needs separate packaging/deploy step).

---

## 4) Azure Monitor — Observability (logs + dashboards)

### Demo: drift + data quality as an Azure ML job

This avoids preview “Azure ML Monitoring” APIs and still gives you a great observability story.

```powershell
python .\02-observability\submit_drift_job.py
```

Then show in Azure ML Studio (experiment `observability`):
- Metrics: `psi_mean`, `psi_p95`, `jsd_mean`, `jsd_p95`, null rates
- Artifacts: `drift_report.json`

### Demo: Azure Monitor queries

Use [02-observability/azure_monitor_queries.kql](02-observability/azure_monitor_queries.kql) in Log Analytics.

---

## 5) Application Insights — Endpoint Monitoring

Infra deploy creates Application Insights, but your endpoint needs to emit telemetry.

Workshop demo options:
- **Option A (fast):** Show App Insights resource exists + explain how to instrument scoring.
- **Option B (full):** Deploy an instrumented endpoint (custom `score.py`) that logs requests/latency to App Insights.

If you want Option B, I can add an `02-observability/inference/` deployment that sets `APPLICATIONINSIGHTS_CONNECTION_STRING`.

---

## 6) Key Vault — Secrets Management

Infra deploy creates Key Vault (RBAC enabled). Demo ideas:
- Show Key Vault exists + RBAC model
- Store secrets like API tokens/connection strings (if needed)
- Reference secrets in your deployment/job via env vars (workshop-friendly)

---

## 7) Azure Container Registry — Docker Images

Infra deploy creates ACR. Demo ideas:
- Show ACR exists + repositories
- (Optional) Build + push a simple inference image and use it for an endpoint deployment

---

## 8) Azure ML Feature Store — Shared Feature Management (optional)

This repo includes an Azure-only, runnable path:

### Provision the Feature Store workspace

```bash
az deployment group create \
  --resource-group rg-dnd-mlops-demo \
  --template-file infra/feature_store.bicep
```

### Register entity + feature set

```powershell
$env:AZURE_FEATURE_STORE_WORKSPACE = "fs-dndmlops-dev"
python .\04-feature-store\register_feature_assets.py
```

Demo in Studio:
- Entities: `document`
- Feature sets: `document_features`

---

## Presenter checklist (15 min before)

- Confirm quotas for `Standard_DS3_v2` in the region
- Confirm you can create managed online endpoints
- Confirm `az login` works on presenter machine
- Confirm you can open Azure ML Studio
