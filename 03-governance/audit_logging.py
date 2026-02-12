"""
Governance and Audit Logging for Azure ML
Demonstrates: Model lineage, audit trails, and compliance reporting
"""

from azure.ai.ml import MLClient
from azure.ai.ml.entities import Model, Environment
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.mgmt.monitor import MonitorManagementClient
from datetime import datetime, timedelta
import json
import os

# =============================================================================
# CONFIGURATION
# =============================================================================

SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP", "rg-dnd-mlops-demo")
WORKSPACE_NAME = os.getenv("AZURE_ML_WORKSPACE", "mlw-dndmlops2-dev")

if not SUBSCRIPTION_ID:
    raise ValueError(
        "Missing AZURE_SUBSCRIPTION_ID. Set it as an environment variable before running this script."
    )

try:
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    credential.get_token("https://management.azure.com/.default")
except Exception:
    credential = InteractiveBrowserCredential()

ml_client = MLClient(credential, SUBSCRIPTION_ID, RESOURCE_GROUP, WORKSPACE_NAME)


# =============================================================================
# MODEL REGISTRATION WITH GOVERNANCE METADATA
# =============================================================================

def register_model_with_governance(
    model_path: str,
    model_name: str,
    training_job_id: str,
    data_version: str,
    author: str,
    approver: str = None,
):
    """
    Register a model with full governance metadata.
    
    This ensures traceability: WHO created it, WHAT data was used,
    WHEN it was created, and WHY it was approved.
    """
    
    model = Model(
        path=model_path,
        name=model_name,
        description=f"Model trained from job {training_job_id}",
        type="mlflow_model",  # Ensures MLflow compatibility
        tags={
            # WHO
            "author": author,
            "approved_by": approver or "pending_approval",
            "team": "ai-centre",
            
            # WHAT
            "data_version": data_version,
            "training_job_id": training_job_id,
            
            # WHEN
            "created_date": datetime.utcnow().isoformat(),
            "approval_date": datetime.utcnow().isoformat() if approver else "",
            
            # WHY
            "approval_reason": "Performance metrics exceed production baseline",
            "use_case": "document_classification",
            
            # COMPLIANCE
            "data_classification": "unclassified",
            "pii_processed": "false",
            "retention_policy": "2_years",
        },
        properties={
            # Performance metrics
            "accuracy": "0.94",
            "precision": "0.93",
            "recall": "0.95",
            "f1_score": "0.94",
            "auc": "0.97",
            
            # Comparison to baseline
            "baseline_accuracy": "0.91",
            "improvement_percent": "3.3",
        },
    )
    
    registered_model = ml_client.models.create_or_update(model)
    print(f"Model registered: {registered_model.name}:{registered_model.version}")
    
    return registered_model


# =============================================================================
# AUDIT LOG QUERIES
# =============================================================================

def get_deployment_audit_log(
    days_back: int = 30,
    operation_type: str = "deployments",
    max_entries: int = 200,
):
    """
    Query Azure Activity Log for deployment operations.
    
    Returns: List of deployment events with who/what/when
    """
    
    monitor_client = MonitorManagementClient(credential, SUBSCRIPTION_ID)
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days_back)
    
    # Filter for ML workspace operations
    filter_str = (
        f"eventTimestamp ge '{start_time.isoformat()}' "
        f"and eventTimestamp le '{end_time.isoformat()}' "
        f"and resourceGroupName eq '{RESOURCE_GROUP}' "
    )
    
    operation_name_value = None
    if operation_type == "deployments":
        operation_name_value = "Microsoft.MachineLearningServices/workspaces/onlineEndpoints/deployments/write"
    elif operation_type == "models":
        operation_name_value = "Microsoft.MachineLearningServices/workspaces/models/write"

    # Query activity log. Some tenants reject filtering by operationName/operationName.value,
    # so we always filter by operation client-side.
    activity_logs = monitor_client.activity_logs.list(filter=filter_str)
    
    audit_entries = []
    for log in activity_logs:
        rp_val = None
        if getattr(log, "resource_provider_name", None) is not None:
            rp_val = getattr(log.resource_provider_name, "value", None)
        if rp_val and rp_val != "Microsoft.MachineLearningServices":
            continue
        if operation_name_value:
            op_val = None
            if getattr(log, "operation_name", None) is not None:
                op_val = getattr(log.operation_name, "value", None)
            if op_val and op_val != operation_name_value:
                continue
        entry = {
            "timestamp": log.event_timestamp.isoformat(),
            "operation": log.operation_name.localized_value,
            "status": log.status.value,
            "caller": log.caller,
            "resource": log.resource_id,
            "correlation_id": log.correlation_id,
        }
        audit_entries.append(entry)
        if max_entries and len(audit_entries) >= max_entries:
            break
        
    return audit_entries


def generate_audit_report(days_back: int = 30):
    """
    Generate a comprehensive audit report for compliance.
    """
    
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "period_days": days_back,
        "workspace": WORKSPACE_NAME,
        "resource_group": RESOURCE_GROUP,
        "sections": {}
    }
    
    # 1. Model Registrations
    print("Fetching model registration events...")
    report["sections"]["model_registrations"] = get_deployment_audit_log(
        days_back=days_back,
        operation_type="models"
    )
    
    # 2. Deployments
    print("Fetching deployment events...")
    report["sections"]["deployments"] = get_deployment_audit_log(
        days_back=days_back,
        operation_type="deployments"
    )
    
    # 3. Current Models in Registry
    print("Fetching current models...")
    models = ml_client.models.list()
    report["sections"]["registered_models"] = [
        {
            "name": m.name,
            "version": m.version,
            "created_time": m.creation_context.created_at.isoformat() if m.creation_context else None,
            "tags": m.tags,
        }
        for m in models
    ]
    
    # 4. Active Endpoints
    print("Fetching active endpoints...")
    endpoints = ml_client.online_endpoints.list()
    report["sections"]["active_endpoints"] = [
        {
            "name": e.name,
            "provisioning_state": e.provisioning_state,
            "created_time": e.creation_context.created_at.isoformat() if e.creation_context else None,
        }
        for e in endpoints
    ]
    
    return report


# =============================================================================
# LOG ANALYTICS KQL QUERIES
# =============================================================================

KQL_QUERIES = {
    "model_deployments": """
    AzureActivity
    | where ResourceProvider == "MICROSOFT.MACHINELEARNINGSERVICES"
    | where OperationNameValue contains "deployments/write"
    | project TimeGenerated, Caller, OperationNameValue, ResourceGroup, 
              CorrelationId, ActivityStatusValue
    | order by TimeGenerated desc
    """,
    
    "model_registrations": """
    AzureActivity
    | where ResourceProvider == "MICROSOFT.MACHINELEARNINGSERVICES"
    | where OperationNameValue contains "models/write"
    | project TimeGenerated, Caller, OperationNameValue, ResourceGroup,
              CorrelationId, ActivityStatusValue
    | order by TimeGenerated desc
    """,
    
    "failed_operations": """
    AzureActivity
    | where ResourceProvider == "MICROSOFT.MACHINELEARNINGSERVICES"
    | where ActivityStatusValue == "Failed"
    | project TimeGenerated, Caller, OperationNameValue, ResourceGroup,
              CorrelationId, ActivityStatusValue, Properties
    | order by TimeGenerated desc
    """,
    
    "user_activity_summary": """
    AzureActivity
    | where ResourceProvider == "MICROSOFT.MACHINELEARNINGSERVICES"
    | where TimeGenerated > ago(30d)
    | summarize OperationCount = count() by Caller, OperationNameValue
    | order by OperationCount desc
    """,
}


# =============================================================================
# AZURE POLICY DEFINITIONS FOR ML GOVERNANCE
# =============================================================================

def get_ml_policy_definitions():
    """
    Returns recommended Azure Policy definitions for ML governance.
    """
    
    policies = [
        {
            "name": "require-private-endpoint",
            "display_name": "Azure ML workspaces should use private endpoints",
            "description": "Ensures all ML workspaces are configured with private endpoints",
            "effect": "Deny",
        },
        {
            "name": "require-managed-identity",
            "display_name": "Azure ML compute should use managed identity",
            "description": "Ensures compute clusters use managed identity for authentication",
            "effect": "Deny",
        },
        {
            "name": "require-encryption",
            "display_name": "Azure ML workspaces should use customer-managed keys",
            "description": "Ensures encryption at rest with CMK",
            "effect": "Audit",
        },
        {
            "name": "allowed-compute-sizes",
            "display_name": "Allowed VM sizes for Azure ML compute",
            "description": "Restricts compute to approved VM sizes for cost control",
            "effect": "Deny",
        },
    ]
    
    return policies


if __name__ == "__main__":
    # Generate audit report
    print("=" * 60)
    print("Generating Audit Report")
    print("=" * 60)
    
    report = generate_audit_report(days_back=30)
    
    # Save report
    report_path = "audit_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nAudit report saved to: {report_path}")
    print(f"Model registrations: {len(report['sections'].get('model_registrations', []))}")
    print(f"Deployments: {len(report['sections'].get('deployments', []))}")
    print(f"Registered models: {len(report['sections'].get('registered_models', []))}")
    print(f"Active endpoints: {len(report['sections'].get('active_endpoints', []))}")
