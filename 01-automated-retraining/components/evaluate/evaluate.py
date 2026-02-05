import argparse
import json
from pathlib import Path

import pandas as pd
import mlflow
from sklearn.metrics import accuracy_score, f1_score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to MLflow model folder")
    parser.add_argument("--test_data", required=True, help="Folder containing test.csv")
    parser.add_argument("--min_accuracy", type=float, default=0.90)
    parser.add_argument("--report_output", required=True)
    parser.add_argument("--deploy_flag", required=True)
    args = parser.parse_args()

    test_path = Path(args.test_data) / "test.csv"
    df = pd.read_csv(test_path)
    if "label" not in df.columns:
        raise ValueError("Expected 'label' column")

    X = df.drop(columns=["label"])
    y = df["label"].astype(int)

    model = mlflow.pyfunc.load_model(args.model)
    y_pred = model.predict(X)

    acc = float(accuracy_score(y, y_pred))
    f1 = float(f1_score(y, y_pred))

    approved = acc >= args.min_accuracy

    report = {
        "accuracy": acc,
        "f1_score": f1,
        "min_accuracy": args.min_accuracy,
        "approved": approved,
    }

    report_path = Path(args.report_output)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2))

    flag_path = Path(args.deploy_flag)
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    flag_path.write_text("1" if approved else "0")

    print("Evaluation report:")
    print(json.dumps(report, indent=2))
    print("Approved:", approved)


if __name__ == "__main__":
    main()
