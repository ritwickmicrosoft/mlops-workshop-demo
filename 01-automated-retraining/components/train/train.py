import argparse
import json
import os
from pathlib import Path

import mlflow
import pandas as pd
from mlflow.models import infer_signature
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Folder containing train.csv and test.csv")
    parser.add_argument("--n_estimators", type=int, default=200)
    parser.add_argument("--max_depth", type=int, default=12)
    parser.add_argument("--random_state", type=int, default=42)
    parser.add_argument("--model_output", required=True)
    parser.add_argument("--metrics_output", required=True)
    parser.add_argument("--registered_model_name", default="spam-classifier")
    args = parser.parse_args()

    data_dir = Path(args.data)
    train_path = data_dir / "train.csv"
    test_path = data_dir / "test.csv"

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    if "label" not in train_df.columns:
        raise ValueError("Expected 'label' column")

    X_train = train_df.drop(columns=["label"])
    y_train = train_df["label"].astype(int)

    X_test = test_df.drop(columns=["label"])
    y_test = test_df["label"].astype(int)

    params = {
        "n_estimators": args.n_estimators,
        "max_depth": args.max_depth,
        "random_state": args.random_state,
        "n_jobs": -1,
    }

    # Azure ML usually injects tracking URI automatically; allow override.
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_param("training_rows", len(train_df))
        mlflow.log_param("test_rows", len(test_df))
        mlflow.log_param("features", X_train.shape[1])

        model = RandomForestClassifier(**params)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred)),
            "recall": float(recall_score(y_test, y_pred)),
            "f1_score": float(f1_score(y_test, y_pred)),
            "roc_auc": float(roc_auc_score(y_test, y_proba)),
        }

        mlflow.log_metrics(metrics)

        signature = infer_signature(X_train, model.predict(X_train))

        # Save MLflow model to pipeline output
        model_out = Path(args.model_output)
        model_out.mkdir(parents=True, exist_ok=True)

        mlflow.sklearn.save_model(model, path=str(model_out), signature=signature)

        # Also register into Azure ML model registry via MLflow, so the workshop can demo governance.
        # If registration fails (permissions, etc.), keep the run successful.
        try:
            mlflow.sklearn.log_model(
                model,
                artifact_path="model",
                signature=signature,
                registered_model_name=args.registered_model_name,
            )
        except Exception as e:
            print(f"WARN: MLflow registration skipped/failed: {e}")

        # Write metrics JSON
        metrics_path = Path(args.metrics_output)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, indent=2))

        print("Run ID:", run.info.run_id)
        print("Metrics:", metrics)


if __name__ == "__main__":
    main()
