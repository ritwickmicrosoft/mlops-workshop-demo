"""Submit the automated retraining pipeline end-to-end.

Workshop-safe behavior:
- The pipeline fetches OpenML Spambase inside the Azure ML job
- No local dataset uploads are required (avoids storage key/SAS restrictions)

Usage (PowerShell):
    $env:AZURE_SUBSCRIPTION_ID = "..."
    $env:AZURE_RESOURCE_GROUP = "rg-dnd-mlops-demo"
    $env:AZURE_ML_WORKSPACE = "mlw-<something>-dev"
    python ./01-automated-retraining/submit_pipeline.py
"""

import os
import time
from pathlib import Path

from pipeline import ml_client, retraining_pipeline


def main() -> None:
    run_suffix = time.strftime("%Y%m%d-%H%M%S")
    experiment_name = os.getenv("AML_EXPERIMENT_NAME", "automated-retraining")

    pipeline_job = retraining_pipeline(
        n_estimators=int(os.getenv("N_ESTIMATORS", "200")),
        max_depth=int(os.getenv("MAX_DEPTH", "12")),
        min_accuracy=float(os.getenv("MIN_ACCURACY", "0.90")),
        noise_std=float(os.getenv("NOISE_STD", "0.0")),
        model_name=os.getenv("MODEL_NAME", "dnd-classification-model"),
    )

    created = ml_client.jobs.create_or_update(
        pipeline_job,
        experiment_name=experiment_name,
    )

    print("Pipeline submitted:", created.name)
    print("Studio URL:", created.studio_url)


if __name__ == "__main__":
    main()
