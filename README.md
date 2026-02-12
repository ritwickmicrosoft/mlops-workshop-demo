# MLOps Workshop Demo

End-to-end Azure ML + MLflow hands-on workshop demonstrating production MLOps patterns.

## 🎯 What You'll Learn

| Module | Topic | Key Concepts | Azure Services | Difficulty |
|--------|-------|--------------|----------------|------------|
| 1 | Environment Setup | SDK auth, workspace config | Azure ML Workspace, Key Vault | Beginner |
| 2 | Train & Track with MLflow | Experiment runs, metrics, artifacts | MLflow Tracking, Model Registry | Beginner |
| 3 | Batch Endpoint Deployment | Model deployment, scoring | Batch Endpoints, Compute Clusters | Intermediate |
| 4 | Automated Retraining Pipeline | Pipeline components, orchestration | Azure ML Pipelines | Intermediate |
| 5 | Drift Detection (Observability) | PSI, JSD, data quality metrics | Jobs, Metrics Logging | Intermediate |
| 6 | Governance & Audit Logging | Activity logs, compliance | Azure Monitor, RBAC | Beginner |

## 📁 Project Structure

```
├── notebooks/
│   └── 01_azure_ml_mlflow_quickstart.ipynb   # Main workshop notebook
├── 01-automated-retraining/                   # Retraining pipeline
│   ├── pipeline.py                            # Azure ML pipeline definition
│   ├── submit_pipeline.py                     # Submit pipeline job
│   ├── simulate_event_trigger.py              # Event-driven retrain demo
│   └── components/                            # Pipeline steps (prep/train/evaluate/register)
├── 02-observability/                          # Drift detection & data quality
│   ├── drift_report.py                        # PSI/JSD drift metrics (runs as Azure ML job)
│   ├── submit_drift_job.py                    # Submit drift job to Azure ML
│   ├── generate_html_report.py                # Generate Observability_Report.html from JSON
│   ├── monitoring_setup.py                    # Azure Monitor integration helpers
│   └── azure_monitor_queries.kql              # Log Analytics KQL queries
├── 03-governance/                             # Audit & compliance
│   ├── audit_logging.py                       # Azure Activity Log queries + model inventory
│   ├── run_audit_report.py                    # Generate audit_report.json + Governance_Report.html
│   └── generate_html_report.py                # Generate Governance_Report.html from JSON
├── 04-feature-store/                          # Feature store assets (advanced)
├── infra/                                     # Bicep templates (with RBAC role assignments)
│   ├── main.bicep                             # Core infra (ML workspace, storage, KV, ACR, compute)
│   └── feature_store.bicep                    # Feature store workspace
├── MLOps_Workshop_Playbook.html               # Interactive workshop guide
└── requirements.txt                           # Pinned Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Azure subscription with Contributor access
- Python 3.11.x recommended (tested with `.venv311`; 3.9+ may work)
- VS Code with Python & Jupyter extensions
- Azure CLI (`az login`)

### 1. Setup Environment

```powershell
# Clone repo
git clone https://github.com/ritwickmicrosoft/mlops-workshop-demo.git
cd mlops-workshop-demo

# Create virtual environment
python -m venv .venv311
.venv311\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Azure

```powershell
az login
$env:AZURE_SUBSCRIPTION_ID = "<your-subscription-id>"
$env:AZURE_RESOURCE_GROUP = "rg-dnd-mlops-demo"
$env:AZURE_ML_WORKSPACE = "mlw-dndmlops2-dev"
```

### 3. Run the Workshop

**Option A: Interactive Playbook** (recommended)
- Open the [**Workshop Playbook**](https://htmlpreview.github.io/?https://github.com/ritwickmicrosoft/mlops-workshop-demo/blob/main/MLOps_Workshop_Playbook.html) in your browser
- Follow the step-by-step guide with checkboxes

**Option B: Notebook Only**
- Open `notebooks/01_azure_ml_mlflow_quickstart.ipynb`
- Run cells sequentially

## ⚠️ Known Issues & Fixes

### NumPy 2.x Compatibility
MLflow models logged with NumPy 2.x fail on Azure ML endpoints (which use NumPy 1.x).

**Fix:** Re-log the model with explicit pip requirements:
```python
mlflow.sklearn.log_model(
    model,
    artifact_path='model',
    pip_requirements=['numpy<2.0', 'scikit-learn>=1.0,<2.0', 'mlflow'],
)
```

See notebook cells 11-12 for the complete fix.

## 📊 Key Metrics

### Drift Detection (Module 5)

Run the drift job and generate an HTML report:
```powershell
python .\02-observability\submit_drift_job.py        # Submit to Azure ML
# After job completes, download the JSON artifact, then:
python .\02-observability\generate_html_report.py --json_path <drift_output.json>
# Opens Observability_Report.html with drift gauges, per-feature table, risk badges
```

| Metric | Low Risk | Medium | High Risk |
|--------|----------|--------|----------|
| **PSI** (Population Stability Index) | < 0.1 | 0.1-0.25 | > 0.25 |
| **JSD** (Jensen-Shannon Divergence) | < 0.05 | 0.05-0.1 | > 0.1 |

### Governance & Audit (Module 6)

Run the audit report (generates both JSON and HTML automatically):
```powershell
python .\03-governance\run_audit_report.py
# Produces audit_report.json + Governance_Report.html
```

## 🔧 Azure Resources

| Resource | Purpose |
|----------|---------|
| Azure ML Workspace | Experiments, models, endpoints |
| Compute Cluster (cpu-cluster) | Training & batch jobs |
| Model Registry | Versioned model storage |
| Batch Endpoint | Asynchronous inference |

## 📚 References

- [Azure ML Documentation](https://learn.microsoft.com/azure/machine-learning/)
- [MLflow with Azure ML](https://learn.microsoft.com/azure/machine-learning/how-to-use-mlflow-cli-runs)
- [Batch Endpoints](https://learn.microsoft.com/azure/machine-learning/concept-endpoints-batch)

## 🧹 Cleanup

```powershell
# Delete batch endpoint
az ml batch-endpoint delete -n spam-batch-* -g $env:AZURE_RESOURCE_GROUP -w $env:AZURE_ML_WORKSPACE --yes

# Delete online endpoint (if created)
az ml online-endpoint delete -n spam-clf-* -g $env:AZURE_RESOURCE_GROUP -w $env:AZURE_ML_WORKSPACE --yes
```

---

**Workshop Playbook:** [**Open Interactive Guide**](https://htmlpreview.github.io/?https://github.com/ritwickmicrosoft/mlops-workshop-demo/blob/main/MLOps_Workshop_Playbook.html)
