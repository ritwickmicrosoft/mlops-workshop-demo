"""Generate a standalone HTML governance & audit report from audit JSON output.

Usage:
  python 03-governance/generate_html_report.py --json_path 03-governance/audit_report.json
  python 03-governance/generate_html_report.py  # uses default path

The script reads the JSON produced by run_audit_report.py and writes
an interactive HTML file with model inventory, deployment events,
endpoint status, and audit trail.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def _status_badge(status: str) -> str:
    s = (status or "").lower()
    if s in ("succeeded", "success", "active", "provisioning succeeded"):
        color = "#27ae60"
    elif s in ("failed", "error"):
        color = "#e74c3c"
    elif s in ("started", "accepted", "creating"):
        color = "#3498db"
    else:
        color = "#6c757d"
    return f'<span style="background:{color};color:#fff;padding:2px 10px;border-radius:12px;font-size:0.82em;">{status}</span>'


def generate_html(report: dict, out_path: Path) -> None:
    sections = report.get("sections", {})
    registered_models = sections.get("registered_models", [])
    deployments = sections.get("deployments", [])
    model_registrations = sections.get("model_registrations", [])
    active_endpoints = sections.get("active_endpoints", [])

    timestamp = report.get("generated_at", datetime.utcnow().isoformat())
    period = report.get("period_days", "—")
    workspace = report.get("workspace", "—")
    rg = report.get("resource_group", "—")

    # Model inventory rows
    model_rows = ""
    for m in registered_models:
        tags = m.get("tags", {}) or {}
        tag_str = ", ".join(f"{k}={v}" for k, v in sorted(tags.items())[:5]) if tags else "—"
        model_rows += f"""
        <tr>
          <td>{m.get('name','—')}</td>
          <td style="text-align:center;">{m.get('version','—')}</td>
          <td>{(m.get('created_time','') or '—')[:19]}</td>
          <td style="font-size:0.8em;">{tag_str}</td>
        </tr>"""

    # Deployment event rows
    deploy_rows = ""
    for d in deployments:
        deploy_rows += f"""
        <tr>
          <td>{(d.get('timestamp','') or '—')[:19]}</td>
          <td>{d.get('operation','—')}</td>
          <td style="text-align:center;">{_status_badge(d.get('status','—'))}</td>
          <td>{d.get('caller','—')}</td>
        </tr>"""

    # Model registration event rows
    reg_rows = ""
    for r in model_registrations:
        reg_rows += f"""
        <tr>
          <td>{(r.get('timestamp','') or '—')[:19]}</td>
          <td>{r.get('operation','—')}</td>
          <td style="text-align:center;">{_status_badge(r.get('status','—'))}</td>
          <td>{r.get('caller','—')}</td>
        </tr>"""

    # Endpoint rows
    endpoint_rows = ""
    for e in active_endpoints:
        endpoint_rows += f"""
        <tr>
          <td>{e.get('name','—')}</td>
          <td style="text-align:center;">{_status_badge(e.get('provisioning_state','—'))}</td>
          <td>{(e.get('created_time','') or '—')[:19]}</td>
        </tr>"""

    # Summary counts
    n_models = len(registered_models)
    n_endpoints = len(active_endpoints)
    n_deploy_events = len(deployments)
    n_reg_events = len(model_registrations)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Governance &amp; Audit Report</title>
<style>
  :root {{ --bg: #f8f9fa; --card: #ffffff; --border: #dee2e6; --text: #212529; --muted: #6c757d; --accent: #0d6efd; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:var(--bg); color:var(--text); padding:24px; }}
  h1 {{ font-size:1.6em; margin-bottom:4px; }}
  .subtitle {{ color:var(--muted); margin-bottom:20px; font-size:0.9em; }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:20px; margin-bottom:20px; }}
  .card h2 {{ font-size:1.15em; margin-bottom:12px; border-bottom:2px solid var(--border); padding-bottom:6px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; }}
  .stat {{ text-align:center; padding:16px; background:#f1f3f5; border-radius:8px; }}
  .stat .val {{ font-size:2em; font-weight:700; color:var(--accent); }}
  .stat .lbl {{ font-size:0.85em; color:var(--muted); }}
  table {{ width:100%; border-collapse:collapse; font-size:0.88em; }}
  th, td {{ padding:8px 10px; border-bottom:1px solid var(--border); text-align:left; }}
  th {{ background:#f1f3f5; font-weight:600; position:sticky; top:0; }}
  tbody tr:hover {{ background:#f8f9fa; }}
  .scroll-table {{ max-height:400px; overflow-y:auto; }}
  .empty {{ text-align:center; padding:24px; color:var(--muted); font-style:italic; }}
  .meta-table {{ font-size:0.85em; }}
  .meta-table td:first-child {{ font-weight:600; width:160px; color:var(--muted); }}
  @media print {{ body {{ padding:10px; }} .card {{ break-inside:avoid; }} }}
</style>
</head>
<body>

<h1>🛡️ Governance &amp; Audit Report</h1>
<div class="subtitle">Generated: {timestamp} &nbsp;|&nbsp; Audit Period: {period} days</div>

<!-- Report Metadata -->
<div class="card">
  <h2>Report Details</h2>
  <table class="meta-table">
    <tr><td>Workspace</td><td>{workspace}</td></tr>
    <tr><td>Resource Group</td><td>{rg}</td></tr>
    <tr><td>Audit Period</td><td>{period} days</td></tr>
    <tr><td>Generated At</td><td>{timestamp}</td></tr>
  </table>
</div>

<!-- Summary -->
<div class="card">
  <h2>Summary</h2>
  <div class="grid">
    <div class="stat"><div class="val">{n_models}</div><div class="lbl">Registered Models</div></div>
    <div class="stat"><div class="val">{n_endpoints}</div><div class="lbl">Active Endpoints</div></div>
    <div class="stat"><div class="val">{n_deploy_events}</div><div class="lbl">Deployment Events</div></div>
    <div class="stat"><div class="val">{n_reg_events}</div><div class="lbl">Registration Events</div></div>
  </div>
</div>

<!-- Registered Models -->
<div class="card">
  <h2>Model Registry Inventory ({n_models} models)</h2>
  {"<div class='scroll-table'><table><thead><tr><th>Model Name</th><th style='text-align:center;'>Version</th><th>Created</th><th>Tags</th></tr></thead><tbody>" + model_rows + "</tbody></table></div>" if model_rows else "<div class='empty'>No models found in the registry.</div>"}
</div>

<!-- Active Endpoints -->
<div class="card">
  <h2>Active Endpoints ({n_endpoints})</h2>
  {"<div class='scroll-table'><table><thead><tr><th>Endpoint Name</th><th style='text-align:center;'>Status</th><th>Created</th></tr></thead><tbody>" + endpoint_rows + "</tbody></table></div>" if endpoint_rows else "<div class='empty'>No active endpoints found.</div>"}
</div>

<!-- Deployment Audit Trail -->
<div class="card">
  <h2>Deployment Audit Trail ({n_deploy_events} events)</h2>
  {"<div class='scroll-table'><table><thead><tr><th>Timestamp</th><th>Operation</th><th style='text-align:center;'>Status</th><th>Caller</th></tr></thead><tbody>" + deploy_rows + "</tbody></table></div>" if deploy_rows else "<div class='empty'>No deployment events found in the audit period.</div>"}
</div>

<!-- Model Registration Audit Trail -->
<div class="card">
  <h2>Model Registration Audit Trail ({n_reg_events} events)</h2>
  {"<div class='scroll-table'><table><thead><tr><th>Timestamp</th><th>Operation</th><th style='text-align:center;'>Status</th><th>Caller</th></tr></thead><tbody>" + reg_rows + "</tbody></table></div>" if reg_rows else "<div class='empty'>No model registration events captured via Activity Log. Note: SDK-based registrations may not appear in Activity Log — check the Model Registry Inventory above.</div>"}
</div>

<!-- Compliance Notes -->
<div class="card">
  <h2>Compliance Notes</h2>
  <ul style="padding-left:20px;font-size:0.9em;line-height:1.8;">
    <li><strong>Activity Log Source:</strong> Azure Monitor Activity Logs (Azure Resource Manager operations)</li>
    <li><strong>SDK-based model registrations</strong> may not generate Activity Log entries — verify via the Model Registry Inventory section above</li>
    <li><strong>Retention:</strong> Activity Logs default to 90 days; configure Log Analytics for longer retention</li>
    <li><strong>RBAC:</strong> Ensure Key Vault uses RBAC authorization (<code>enableRbacAuthorization: true</code>) for auditability</li>
    <li><strong>Diagnostic Settings:</strong> Must be enabled on the ML workspace for audit log capture (see <code>infra/main.bicep</code>)</li>
  </ul>
</div>

</body>
</html>"""

    out_path.write_text(html, encoding="utf-8")
    print(f"HTML report written to: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HTML governance & audit report.")
    parser.add_argument(
        "--json_path",
        default=str(Path(__file__).resolve().parent / "audit_report.json"),
        help="Path to audit_report.json produced by run_audit_report.py.",
    )
    parser.add_argument(
        "--out_html",
        default="",
        help="Output HTML path. Defaults to <json_dir>/Governance_Report.html.",
    )
    args = parser.parse_args()

    json_path = Path(args.json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"Audit JSON not found: {json_path}")

    report = json.loads(json_path.read_text(encoding="utf-8"))

    if args.out_html:
        out = Path(args.out_html)
    else:
        out = json_path.parent / "Governance_Report.html"

    generate_html(report, out)


if __name__ == "__main__":
    main()
