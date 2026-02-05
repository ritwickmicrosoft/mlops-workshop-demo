# DND/CAF MLOps Hackathon Demo

## 🎯 Overview
This repository contains hands-on demos for the MLOps hackathon covering:
1. **Automated Retraining** - Event-driven pipeline triggers
2. **Observability** - Model monitoring dashboards
3. **Governance** - Audit trails and lineage
4. **Feature Stores** - Shared feature management

## 📁 Project Structure
```
├── 01-automated-retraining/      # Automated retraining demo (Azure ML pipeline skeleton)
├── 02-observability/             # Monitoring and dashboards setup examples
├── 03-governance/                # Audit logging and governance examples
├── 04-feature-store/             # Feature store setup examples
├── infra/                        # Infrastructure as Code (Bicep)
└── notebooks/                    # Hands-on notebooks
```

## 🔧 Azure Resources Used
| Resource | Purpose |
|----------|---------|
| Azure Machine Learning | ML workspace, pipelines, model registry |
| Azure Data Factory | Data pipelines, triggers |
| Azure Event Grid | Event-driven automation |
| Azure Monitor | Observability and dashboards |
| Application Insights | Endpoint monitoring |
| Azure Key Vault | Secrets management |
| Azure Container Registry | Docker images |
| Azure ML Feature Store | Shared feature management |

## 🚀 Quick Start

For a single-page, end-to-end, presentation-friendly guide, open:
- [MLOps_Hackathon_Guide.html](MLOps_Hackathon_Guide.html)

### Prerequisites
- Azure Subscription with Contributor access
- Azure CLI installed
- Python 3.9+
- VS Code with Azure ML extension

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repo-url>
cd <repo-folder>

# Create Python environment
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configure Azure Settings (for notebooks)

The notebook [notebooks/01_azure_ml_mlflow_quickstart.ipynb](notebooks/01_azure_ml_mlflow_quickstart.ipynb) reads configuration from environment variables:

- `AZURE_SUBSCRIPTION_ID`
- `AZURE_RESOURCE_GROUP` (default: `rg-dnd-mlops-demo`)
- `AZURE_ML_WORKSPACE` (default: `mlw-dndmlops-dev`)
- `AZURE_FEATURE_STORE_WORKSPACE` (default: `fs-dndmlops-dev`, for Feature Store demos)

PowerShell example:
```powershell
$env:AZURE_SUBSCRIPTION_ID = "<subscription-id>"
$env:AZURE_RESOURCE_GROUP = "rg-dnd-mlops-demo"
$env:AZURE_ML_WORKSPACE = "mlw-dndmlops-dev"
```

### 3. Deploy Infrastructure
```bash
# Login to Azure
az login

# Deploy resources
az deployment group create \
  --resource-group rg-dnd-mlops-demo \
  --template-file infra/main.bicep
```

### 4. Run the Demos

- Start with [notebooks/01_azure_ml_mlflow_quickstart.ipynb](notebooks/01_azure_ml_mlflow_quickstart.ipynb)
- Run automated retraining:
  - [01-automated-retraining/submit_pipeline.py](01-automated-retraining/submit_pipeline.py)
  - [01-automated-retraining/simulate_event_trigger.py](01-automated-retraining/simulate_event_trigger.py)
- Run observability drift/quality job:
  - [02-observability/submit_drift_job.py](02-observability/submit_drift_job.py)
- Run governance audit report:
  - [03-governance/run_audit_report.py](03-governance/run_audit_report.py)
- Follow the numbered folders in order for the remaining hackathon exercises.

## 📚 Hackathon Agenda

### Day 1: Foundations & Automated Retraining
| Time | Topic |
|------|-------|
| 09:00-10:00 | MLOps Overview & Azure ML Setup |
| 10:00-12:00 | Hands-on: MLflow Integration |
| 13:00-15:00 | Hands-on: Automated Retraining Pipeline |
| 15:00-17:00 | CI/CD with GitHub Actions / Azure DevOps |

### Day 2: Observability & Governance
| Time | Topic |
|------|-------|
| 09:00-11:00 | Hands-on: Model Monitoring Setup |
| 11:00-12:00 | Building Dashboards |
| 13:00-15:00 | Hands-on: Feature Store |
| 15:00-17:00 | Governance, RBAC & Audit Logs |

## 🔗 Useful Links
- [Azure ML Documentation](https://docs.microsoft.com/azure/machine-learning/)
- [MLflow on Azure ML](https://docs.microsoft.com/azure/machine-learning/how-to-use-mlflow)
- [Azure ML Feature Store](https://docs.microsoft.com/azure/machine-learning/concept-what-is-managed-feature-store)
- [Azure ML Model Monitoring](https://docs.microsoft.com/azure/machine-learning/how-to-monitor-model-performance)

## 👥 Contact
- **Iliana Meco** - Cloud Solution Architect - ilianameco@microsoft.com
- **Ritwick Dutta** - AI Cloud Solution Architect
