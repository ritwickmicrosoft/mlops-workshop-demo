"""Observability demo entrypoint.

The original version of this file used Azure ML Monitoring preview entities/APIs.
Those APIs are version-sensitive and often break workshops (SDK mismatch, preview
feature availability, required workspace settings).

For a reliable workshop demo, use the supported path implemented in:
- `submit_drift_job.py` (submits an Azure ML job)
- `drift_report.py` (computes drift + quality metrics and logs to MLflow)

Run (PowerShell):
    $env:AZURE_SUBSCRIPTION_ID = "..."
    $env:AZURE_RESOURCE_GROUP = "rg-dnd-mlops-demo"
    $env:AZURE_ML_WORKSPACE = "mlw-dndmlops-dev"
    python ./02-observability/submit_drift_job.py
"""

if __name__ == "__main__":
        from submit_drift_job import main

        main()

