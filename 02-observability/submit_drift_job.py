"""Submit a drift/quality report as an Azure ML job.

This avoids preview monitoring APIs and still lets you demo observability:
- Drift metrics show up as job metrics (MLflow)
- The JSON report is stored as an artifact

Usage (PowerShell):
  $env:AZURE_SUBSCRIPTION_ID = "..."
  $env:AZURE_RESOURCE_GROUP = "rg-dnd-mlops-demo"
  $env:AZURE_ML_WORKSPACE = "mlw-dndmlops-dev"
    python ./02-observability/submit_drift_job.py
"""

from __future__ import annotations

import os
import time

from azure.ai.ml import Output, MLClient, command
from azure.identity import DefaultAzureCredential


def main() -> None:
    sub = os.getenv("AZURE_SUBSCRIPTION_ID", "").strip()
    rg = os.getenv("AZURE_RESOURCE_GROUP", "rg-dnd-mlops-demo").strip()
    ws = os.getenv("AZURE_ML_WORKSPACE", "mlw-dndmlops-dev").strip()

    if not sub:
        raise ValueError("Missing AZURE_SUBSCRIPTION_ID")

    ml_client = MLClient(DefaultAzureCredential(), sub, rg, ws)

    prod_noise_std = float(os.getenv("PROD_NOISE_STD", "0.01"))
    run_suffix = time.strftime("%Y%m%d-%H%M%S")

    job = command(
        name=f"drift-report-{run_suffix}",
        display_name=f"Drift + Quality Report ({run_suffix})",
        code="./02-observability",
        command=(
            "python drift_report.py "
            "--openml_data_id 44 "
            "--baseline_noise_std 0.0 "
            f"--production_noise_std {prod_noise_std} "
            "--out_json ${{outputs.report}}"
        ),
        outputs={
            "report": Output(type="uri_file")
        },
        environment="azureml://registries/azureml/environments/sklearn-1.5/labels/latest",
        compute="cpu-cluster",
    )

    created = ml_client.jobs.create_or_update(job, experiment_name="observability")
    print("Job submitted:", created.name)
    print("Studio URL:", created.studio_url)


if __name__ == "__main__":
    main()
