# Observability — Drift Detection & Data Quality

This module computes data drift and data quality metrics between a baseline (training) dataset and a simulated production dataset, logs them to MLflow, and generates an interactive HTML report.

## What It Does

1. **`drift_report.py`** — Runs as an Azure ML job (or locally). Computes:
   - **PSI** (Population Stability Index) — measures distribution shift per feature
   - **JSD** (Jensen-Shannon Divergence) — symmetric distance between distributions
   - **Null rates** — baseline vs production data quality
   - Outputs `drift_output.json` + logs metrics to MLflow

2. **`submit_drift_job.py`** — Submits `drift_report.py` as an Azure ML command job on `cpu-cluster` using the `sklearn-1.5` curated environment.

3. **`generate_html_report.py`** — Converts the drift JSON into a standalone `Observability_Report.html` with:
   - Overall risk banner (Low / Medium / High)
   - Aggregate drift gauges (PSI mean/p95, JSD mean/p95)
   - Per-feature drift table sorted by PSI with risk badges
   - Data quality summary (null rates, column counts)
   - Interpretation guide with threshold definitions

## Quick Start

```powershell
# 1. Submit the drift job to Azure ML
python .\02-observability\submit_drift_job.py

# 2. After job completes, download the JSON artifact from Azure ML Studio
#    (Jobs → observability → <job> → Outputs + logs → report)

# 3. Generate the HTML report locally
python .\02-observability\generate_html_report.py --json_path <path-to-drift_output.json>

# 4. Open Observability_Report.html in your browser
```

## Risk Thresholds

| Metric | Low Risk | Medium | High Risk |
|--------|----------|--------|-----------|
| **PSI** | < 0.1 | 0.1–0.25 | > 0.25 |
| **JSD** | < 0.05 | 0.05–0.1 | > 0.1 |

## Where to See Results

- **Azure ML Studio** → Jobs → `observability` experiment → Select job → **Metrics** tab (PSI/JSD/null rates)
- **Locally** → Open `Observability_Report.html` in any browser

## Other Files

| File | Purpose |
|------|---------|
| `monitoring_setup.py` | Helper for Azure Monitor integration |
| `azure_monitor_queries.kql` | Log Analytics KQL queries for ML operations |
