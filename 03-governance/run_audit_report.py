"""Workshop helper to generate an audit report.

This wraps `audit_logging.generate_audit_report()` and prints quick links.

Usage (PowerShell):
  $env:AZURE_SUBSCRIPTION_ID = "..."
  $env:AZURE_RESOURCE_GROUP = "rg-dnd-mlops-demo"
  $env:AZURE_ML_WORKSPACE = "mlw-dndmlops-dev"
  python .\03-governance\run_audit_report.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from audit_logging import generate_audit_report


def main() -> None:
    days_back = int(os.getenv("AUDIT_DAYS_BACK", "7"))
    report = generate_audit_report(days_back=days_back)

    out = Path(__file__).resolve().parent / "audit_report.json"
    out.write_text(json.dumps(report, indent=2, default=str))

    print("Wrote:", out)
    print("Period days:", days_back)
    print("Model registrations:", len(report["sections"].get("model_registrations", [])))
    print("Deployments:", len(report["sections"].get("deployments", [])))
    print("Registered models:", len(report["sections"].get("registered_models", [])))
    print("Active endpoints:", len(report["sections"].get("active_endpoints", [])))

    # Auto-generate HTML report alongside the JSON
    try:
        from generate_html_report import generate_html
        html_path = out.with_suffix(".html")
        generate_html(report, html_path)
    except Exception as e:
        print(f"[WARN] Could not generate HTML report: {e}")


if __name__ == "__main__":
    main()
