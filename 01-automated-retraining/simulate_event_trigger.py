"""Simulate an event-driven retraining trigger.

This is a workshop-friendly stand-in for Event Grid + Azure Function:
- Submit the retraining pipeline with a dataset variation (adds small noise)

Later, you can wire this script into an Azure Function triggered by BlobCreated.

Usage:
  $env:AZURE_SUBSCRIPTION_ID = "..."
    python ./01-automated-retraining/simulate_event_trigger.py
"""

import os
import time
from pathlib import Path

from pipeline import ml_client, retraining_pipeline


def main() -> None:
    run_suffix = time.strftime("%Y%m%d-%H%M%S")
    experiment_name = os.getenv("AML_EXPERIMENT_NAME", "automated-retraining")

    noise_std = float(os.getenv("TRIGGER_NOISE_STD", "0.005"))
    _ = Path(__file__).resolve().parent  # keeps parity with other scripts

    pipeline_job = retraining_pipeline(
        n_estimators=int(os.getenv("N_ESTIMATORS", "200")),
        max_depth=int(os.getenv("MAX_DEPTH", "12")),
        min_accuracy=float(os.getenv("MIN_ACCURACY", "0.90")),
        noise_std=noise_std,
        model_name=os.getenv("MODEL_NAME", "dnd-classification-model"),
    )

    created = ml_client.jobs.create_or_update(
        pipeline_job,
        experiment_name=experiment_name,
    )

    print("Simulated event trigger submitted pipeline:")
    print("Job:", created.name)
    print("Studio URL:", created.studio_url)


if __name__ == "__main__":
    main()
