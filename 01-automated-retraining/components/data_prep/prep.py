import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import fetch_openml


def _resolve_input_path(raw_data: str) -> Path:
    p = Path(raw_data)
    if p.is_file():
        return p
    if p.is_dir():
        # pick first csv in folder
        csvs = sorted(p.glob('*.csv'))
        if not csvs:
            raise FileNotFoundError(f"No .csv found in folder: {p}")
        return csvs[0]
    raise FileNotFoundError(f"raw_data path not found: {raw_data}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw_data",
        required=False,
        default=None,
        help="Optional CSV path (file/folder). If omitted, fetches OpenML Spambase.",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--test_size", type=float, default=0.2)
    parser.add_argument("--random_state", type=int, default=42)
    parser.add_argument(
        "--noise_std",
        type=float,
        default=0.0,
        help="Std-dev of Gaussian noise applied to numeric features (simulates drift).",
    )
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    input_name = "openml:spambase"
    if args.raw_data:
        input_file = _resolve_input_path(args.raw_data)
        df = pd.read_csv(input_file)
        input_name = input_file.name
    else:
        # Use try/except for sklearn version compatibility
        # parser="auto" was added in sklearn 1.2+
        try:
            spambase = fetch_openml(data_id=44, as_frame=True, parser="auto")
        except TypeError:
            # Fallback for sklearn < 1.2
            spambase = fetch_openml(data_id=44, as_frame=True)
        df = spambase.frame.rename(columns={"class": "label"})

    if "label" not in df.columns:
        raise ValueError("Expected a 'label' column in input CSV")

    # Ensure numeric label
    df["label"] = df["label"].astype(int)

    # Optional noise to mimic drift
    if args.noise_std and args.noise_std > 0:
        feature_cols = [c for c in df.columns if c != "label"]
        rng = np.random.default_rng(args.random_state)
        noise = rng.normal(loc=0.0, scale=args.noise_std, size=(len(df), len(feature_cols)))
        df.loc[:, feature_cols] = df[feature_cols].astype(float).values + noise

    # Shuffle + split
    df = df.sample(frac=1.0, random_state=args.random_state).reset_index(drop=True)
    split_idx = int(len(df) * (1.0 - args.test_size))
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    train_path = out_dir / "train.csv"
    test_path = out_dir / "test.csv"
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    # Write a tiny manifest for downstream steps
    (out_dir / "manifest.txt").write_text(
        f"input={input_name}\nrows={len(df)}\ntrain={len(train_df)}\ntest={len(test_df)}\nnoise_std={args.noise_std}\n"
    )

    print(f"Wrote: {train_path}")
    print(f"Wrote: {test_path}")


if __name__ == "__main__":
    main()
