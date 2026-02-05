import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy_flag", required=True)
    parser.add_argument("--model_name", required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()

    flag = Path(args.deploy_flag).read_text().strip()
    if flag != "1":
        print("Model not approved; skipping registration step.")
        return

    # Registration is handled in the train step via MLflow registration.
    # This component exists to demonstrate an approval gate in a pipeline.
    print(f"Model approved for deployment. Model name: {args.model_name}")
    print(f"Model path: {args.model}")


if __name__ == "__main__":
    main()
