"""Compute lightweight data drift + data quality metrics.

This is intentionally workshop-friendly:
- Uses only pandas/numpy (no preview Azure ML Monitoring APIs)
- Logs metrics to MLflow so you can show results in Azure ML Studio

Inputs (two modes):
1) File mode:
    - baseline_csv: reference dataset (e.g., training data)
    - production_csv: current dataset (e.g., recent inference inputs or new batch)
2) Generated mode (secure-workspace friendly):
    - openml_data_id + baseline_noise_std + production_noise_std

Assumes a binary classification dataset with a `label` column (0/1), but will
compute drift for all non-label columns.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
from sklearn.datasets import fetch_openml


def _load_openml_spambase(data_id: int = 44) -> pd.DataFrame:
    # Use try/except for sklearn version compatibility
    # parser="auto" was added in sklearn 1.2+
    try:
        spambase = fetch_openml(data_id=data_id, as_frame=True, parser="auto")
    except TypeError:
        # Fallback for sklearn < 1.2
        spambase = fetch_openml(data_id=data_id, as_frame=True)
    df = spambase.frame.rename(columns={"class": "label"})
    df["label"] = df["label"].astype(int)
    return df


def _apply_gaussian_noise(df: pd.DataFrame, noise_std: float, seed: int = 123) -> pd.DataFrame:
    if noise_std <= 0:
        return df

    feature_cols = [c for c in df.columns if c != "label"]
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, noise_std, size=(len(df), len(feature_cols)))
    df_out = df.copy()
    df_out.loc[:, feature_cols] = df_out[feature_cols].astype(float).values + noise
    return df_out


def _psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index for numeric arrays."""
    expected = expected[np.isfinite(expected)]
    actual = actual[np.isfinite(actual)]
    if expected.size == 0 or actual.size == 0:
        return float("nan")

    quantiles = np.linspace(0, 1, bins + 1)
    breakpoints = np.unique(np.quantile(expected, quantiles))
    if breakpoints.size < 3:
        return 0.0

    expected_counts, _ = np.histogram(expected, bins=breakpoints)
    actual_counts, _ = np.histogram(actual, bins=breakpoints)

    expected_pct = expected_counts / max(expected_counts.sum(), 1)
    actual_pct = actual_counts / max(actual_counts.sum(), 1)

    eps = 1e-6
    expected_pct = np.clip(expected_pct, eps, 1)
    actual_pct = np.clip(actual_pct, eps, 1)

    return float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))


def _js_divergence(p: np.ndarray, q: np.ndarray) -> float:
    eps = 1e-12
    p = np.clip(p, eps, 1)
    q = np.clip(q, eps, 1)
    m = 0.5 * (p + q)
    return float(0.5 * (np.sum(p * np.log(p / m)) + np.sum(q * np.log(q / m))))


def _hist_jsd(x: np.ndarray, y: np.ndarray, bins: int = 20) -> float:
    x = x[np.isfinite(x)]
    y = y[np.isfinite(y)]
    if x.size == 0 or y.size == 0:
        return float("nan")

    lo = float(min(np.min(x), np.min(y)))
    hi = float(max(np.max(x), np.max(y)))
    if lo == hi:
        return 0.0

    x_hist, edges = np.histogram(x, bins=bins, range=(lo, hi), density=True)
    y_hist, _ = np.histogram(y, bins=edges, density=True)

    x_hist = x_hist / max(x_hist.sum(), 1e-12)
    y_hist = y_hist / max(y_hist.sum(), 1e-12)

    return _js_divergence(x_hist, y_hist)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline_csv")
    parser.add_argument("--production_csv")
    parser.add_argument("--openml_data_id", type=int, default=44)
    parser.add_argument("--baseline_noise_std", type=float, default=0.0)
    parser.add_argument("--production_noise_std", type=float, default=0.01)
    parser.add_argument("--out_json", required=True)
    parser.add_argument("--bins", type=int, default=10)
    args = parser.parse_args()

    if args.baseline_csv and args.production_csv:
        baseline = pd.read_csv(args.baseline_csv)
        prod = pd.read_csv(args.production_csv)
        source_desc = {
            "mode": "files",
            "baseline_csv": Path(args.baseline_csv).name,
            "production_csv": Path(args.production_csv).name,
        }
    else:
        base_df = _load_openml_spambase(data_id=args.openml_data_id)
        baseline = _apply_gaussian_noise(base_df, noise_std=float(args.baseline_noise_std), seed=123)
        prod = _apply_gaussian_noise(base_df, noise_std=float(args.production_noise_std), seed=456)
        source_desc = {
            "mode": "openml",
            "openml_data_id": int(args.openml_data_id),
            "baseline_noise_std": float(args.baseline_noise_std),
            "production_noise_std": float(args.production_noise_std),
        }

    report: dict[str, object] = {
        "baseline_rows": int(len(baseline)),
        "production_rows": int(len(prod)),
        "quality": {},
        "drift": {},
    }

    # Quality checks
    all_cols = sorted(set(baseline.columns).intersection(set(prod.columns)))
    missing_cols = sorted(set(baseline.columns).symmetric_difference(set(prod.columns)))
    report["quality"] = {
        "common_columns": len(all_cols),
        "missing_or_extra_columns": missing_cols,
        "baseline_null_rate": float(baseline[all_cols].isna().mean().mean()) if all_cols else 0.0,
        "production_null_rate": float(prod[all_cols].isna().mean().mean()) if all_cols else 0.0,
    }

    # Drift per numeric feature
    drift_metrics: dict[str, dict[str, float]] = {}
    numeric_cols = [c for c in all_cols if c != "label" and pd.api.types.is_numeric_dtype(baseline[c])]

    for col in numeric_cols:
        b = baseline[col].to_numpy(dtype=float)
        p = prod[col].to_numpy(dtype=float)
        drift_metrics[col] = {
            "psi": _psi(b, p, bins=args.bins),
            "jsd": _hist_jsd(b, p, bins=max(10, args.bins * 2)),
        }

    # Aggregate drift
    psi_values = [v["psi"] for v in drift_metrics.values() if np.isfinite(v["psi"])]
    jsd_values = [v["jsd"] for v in drift_metrics.values() if np.isfinite(v["jsd"])]

    report["drift"] = {
        "num_numeric_features": len(numeric_cols),
        "psi_mean": float(np.mean(psi_values)) if psi_values else float("nan"),
        "psi_p95": float(np.percentile(psi_values, 95)) if psi_values else float("nan"),
        "jsd_mean": float(np.mean(jsd_values)) if jsd_values else float("nan"),
        "jsd_p95": float(np.percentile(jsd_values, 95)) if jsd_values else float("nan"),
        "per_feature": drift_metrics,
    }

    # Log to MLflow
    with mlflow.start_run(run_name="drift-report"):
        for k, v in source_desc.items():
            mlflow.log_param(k, v)
        mlflow.log_metric("baseline_null_rate", report["quality"]["baseline_null_rate"])  # type: ignore[index]
        mlflow.log_metric("production_null_rate", report["quality"]["production_null_rate"])  # type: ignore[index]
        mlflow.log_metric("psi_mean", report["drift"]["psi_mean"])  # type: ignore[index]
        mlflow.log_metric("psi_p95", report["drift"]["psi_p95"])  # type: ignore[index]
        mlflow.log_metric("jsd_mean", report["drift"]["jsd_mean"])  # type: ignore[index]
        mlflow.log_metric("jsd_p95", report["drift"]["jsd_p95"])  # type: ignore[index]

        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2))
        mlflow.log_artifact(str(out_path))

    print(json.dumps(report, indent=2))

    # Auto-generate HTML report alongside the JSON
    try:
        from generate_html_report import generate_html
        html_path = out_path.with_suffix(".html")
        generate_html(report, html_path)
    except Exception as e:
        print(f"[WARN] Could not generate HTML report: {e}")


if __name__ == "__main__":
    main()
