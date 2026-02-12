"""Generate a standalone HTML observability report from drift JSON output.

Usage:
  python 02-observability/generate_html_report.py --json_path 02-observability/drift_output.json
  python 02-observability/generate_html_report.py  # uses default path

The script reads the JSON produced by drift_report.py and writes
an interactive HTML file with drift gauges, per-feature table, and
data-quality summary.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def _risk_badge(value: float, thresholds: tuple[float, float]) -> str:
    lo, hi = thresholds
    if value < lo:
        color, label = "#27ae60", "Low"
    elif value < hi:
        color, label = "#f39c12", "Medium"
    else:
        color, label = "#e74c3c", "High"
    return f'<span style="background:{color};color:#fff;padding:2px 10px;border-radius:12px;font-size:0.85em;">{label}</span>'


def _psi_badge(v: float) -> str:
    return _risk_badge(v, (0.1, 0.25))


def _jsd_badge(v: float) -> str:
    return _risk_badge(v, (0.05, 0.1))


def _gauge_svg(value: float, max_val: float, label: str, color: str) -> str:
    pct = min(value / max_val, 1.0) * 100
    return f"""
    <div style="text-align:center;min-width:140px;">
      <div style="font-size:0.85em;color:#666;">{label}</div>
      <div style="background:#eee;border-radius:6px;height:18px;margin:4px 0;overflow:hidden;">
        <div style="background:{color};height:100%;width:{pct:.1f}%;border-radius:6px;"></div>
      </div>
      <div style="font-size:1.3em;font-weight:700;">{value:.6f}</div>
    </div>"""


def generate_html(report: dict, out_path: Path) -> None:
    drift = report.get("drift", {})
    quality = report.get("quality", {})
    per_feature = drift.get("per_feature", {})

    psi_mean = drift.get("psi_mean", 0)
    psi_p95 = drift.get("psi_p95", 0)
    jsd_mean = drift.get("jsd_mean", 0)
    jsd_p95 = drift.get("jsd_p95", 0)

    # Per-feature rows
    feature_rows = ""
    for feat, vals in sorted(per_feature.items(), key=lambda x: -x[1].get("psi", 0)):
        psi = vals.get("psi", 0)
        jsd = vals.get("jsd", 0)
        feature_rows += f"""
        <tr>
          <td>{feat}</td>
          <td style="text-align:right;">{psi:.6f}</td>
          <td style="text-align:center;">{_psi_badge(psi)}</td>
          <td style="text-align:right;">{jsd:.6f}</td>
          <td style="text-align:center;">{_jsd_badge(jsd)}</td>
        </tr>"""

    # Overall risk
    if psi_mean < 0.1 and jsd_mean < 0.05:
        overall_color, overall_label = "#27ae60", "No Significant Drift Detected"
    elif psi_mean < 0.25 and jsd_mean < 0.1:
        overall_color, overall_label = "#f39c12", "Moderate Drift — Monitor Closely"
    else:
        overall_color, overall_label = "#e74c3c", "Significant Drift — Action Required"

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Observability Report — Data Drift &amp; Quality</title>
<style>
  :root {{ --bg: #f8f9fa; --card: #ffffff; --border: #dee2e6; --text: #212529; --muted: #6c757d; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:var(--bg); color:var(--text); padding:24px; }}
  h1 {{ font-size:1.6em; margin-bottom:4px; }}
  .subtitle {{ color:var(--muted); margin-bottom:20px; font-size:0.9em; }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:20px; margin-bottom:20px; }}
  .card h2 {{ font-size:1.15em; margin-bottom:12px; border-bottom:2px solid var(--border); padding-bottom:6px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:16px; }}
  .stat {{ text-align:center; padding:16px; }}
  .stat .val {{ font-size:2em; font-weight:700; }}
  .stat .lbl {{ font-size:0.85em; color:var(--muted); }}
  table {{ width:100%; border-collapse:collapse; font-size:0.9em; }}
  th, td {{ padding:8px 10px; border-bottom:1px solid var(--border); text-align:left; }}
  th {{ background:#f1f3f5; font-weight:600; position:sticky; top:0; }}
  tbody tr:hover {{ background:#f8f9fa; }}
  .banner {{ padding:14px 20px; border-radius:8px; font-weight:600; font-size:1.05em; margin-bottom:20px; text-align:center; }}
  .gauge-row {{ display:flex; gap:24px; justify-content:center; flex-wrap:wrap; padding:10px 0; }}
  .threshold-legend {{ display:flex; gap:16px; justify-content:center; flex-wrap:wrap; font-size:0.82em; color:var(--muted); margin-top:10px; }}
  .threshold-legend span {{ display:inline-flex; align-items:center; gap:4px; }}
  .dot {{ width:10px; height:10px; border-radius:50%; display:inline-block; }}
  .scroll-table {{ max-height:420px; overflow-y:auto; }}
  @media print {{ body {{ padding:10px; }} .card {{ break-inside:avoid; }} }}
</style>
</head>
<body>

<h1>📊 Observability Report — Data Drift &amp; Quality</h1>
<div class="subtitle">Generated: {timestamp} &nbsp;|&nbsp; Baseline rows: {report.get('baseline_rows','—')} &nbsp;|&nbsp; Production rows: {report.get('production_rows','—')}</div>

<div class="banner" style="background:{overall_color}22;color:{overall_color};border:1px solid {overall_color}44;">
  {overall_label}
</div>

<!-- Aggregate Metrics -->
<div class="card">
  <h2>Aggregate Drift Metrics</h2>
  <div class="gauge-row">
    {_gauge_svg(psi_mean, 0.5, "PSI Mean", "#3498db")}
    {_gauge_svg(psi_p95, 0.5, "PSI p95", "#2980b9")}
    {_gauge_svg(jsd_mean, 0.2, "JSD Mean", "#9b59b6")}
    {_gauge_svg(jsd_p95, 0.2, "JSD p95", "#8e44ad")}
  </div>
  <div class="threshold-legend">
    <span><span class="dot" style="background:#27ae60;"></span> Low: PSI &lt; 0.1 / JSD &lt; 0.05</span>
    <span><span class="dot" style="background:#f39c12;"></span> Medium: PSI 0.1–0.25 / JSD 0.05–0.1</span>
    <span><span class="dot" style="background:#e74c3c;"></span> High: PSI &gt; 0.25 / JSD &gt; 0.1</span>
  </div>
</div>

<!-- Data Quality -->
<div class="card">
  <h2>Data Quality</h2>
  <div class="grid">
    <div class="stat">
      <div class="val">{quality.get('common_columns', '—')}</div>
      <div class="lbl">Common Columns</div>
    </div>
    <div class="stat">
      <div class="val">{quality.get('baseline_null_rate', 0):.4%}</div>
      <div class="lbl">Baseline Null Rate</div>
    </div>
    <div class="stat">
      <div class="val">{quality.get('production_null_rate', 0):.4%}</div>
      <div class="lbl">Production Null Rate</div>
    </div>
    <div class="stat">
      <div class="val">{len(quality.get('missing_or_extra_columns', []))}</div>
      <div class="lbl">Missing / Extra Columns</div>
    </div>
  </div>
</div>

<!-- Per-Feature Drift -->
<div class="card">
  <h2>Per-Feature Drift ({drift.get('num_numeric_features', 0)} numeric features)</h2>
  <div class="scroll-table">
    <table>
      <thead>
        <tr><th>Feature</th><th style="text-align:right;">PSI</th><th style="text-align:center;">Risk</th><th style="text-align:right;">JSD</th><th style="text-align:center;">Risk</th></tr>
      </thead>
      <tbody>{feature_rows}</tbody>
    </table>
  </div>
</div>

<!-- Interpretation Guide -->
<div class="card">
  <h2>Interpretation Guide</h2>
  <table>
    <thead><tr><th>Metric</th><th>What It Measures</th><th>Low</th><th>Medium</th><th>High</th></tr></thead>
    <tbody>
      <tr><td><strong>PSI</strong></td><td>Population Stability Index — distribution shift between baseline &amp; production</td><td>&lt; 0.1</td><td>0.1 – 0.25</td><td>&gt; 0.25</td></tr>
      <tr><td><strong>JSD</strong></td><td>Jensen-Shannon Divergence — symmetric distance between two distributions</td><td>&lt; 0.05</td><td>0.05 – 0.1</td><td>&gt; 0.1</td></tr>
    </tbody>
  </table>
</div>

</body>
</html>"""

    out_path.write_text(html, encoding="utf-8")
    print(f"HTML report written to: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HTML observability report from drift JSON.")
    parser.add_argument(
        "--json_path",
        default=str(Path(__file__).resolve().parent / "drift_output.json"),
        help="Path to drift_report.py JSON output.",
    )
    parser.add_argument(
        "--out_html",
        default="",
        help="Output HTML path. Defaults to <json_dir>/Observability_Report.html.",
    )
    args = parser.parse_args()

    json_path = Path(args.json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"Drift JSON not found: {json_path}")

    report = json.loads(json_path.read_text(encoding="utf-8"))

    if args.out_html:
        out = Path(args.out_html)
    else:
        out = json_path.parent / "Observability_Report.html"

    generate_html(report, out)


if __name__ == "__main__":
    main()
