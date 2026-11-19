import csv
import io
from datetime import datetime, timezone
from html import escape

from flask import current_app

from backend.services.analytics_service import get_analytics


def build_security_report_csv(
    user_id: int,
    username: str,
    device: dict[str, object],
    network: dict[str, object],
    recommendations: list[dict[str, str]],
) -> bytes:
    analytics = get_analytics(user_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["CyberGuard Personal Security Intelligence Report"])
    writer.writerow(["Version", current_app.config["APP_VERSION"]])
    writer.writerow(["Report generation date", datetime.now(timezone.utc).isoformat()])
    writer.writerow(["Account", username])
    writer.writerow(["Disclaimer", "Collected facts and recommendations only; this is not a complete security audit."])
    writer.writerow([])
    writer.writerow(["COLLECTED DEVICE FACTS"])
    for key in ("operating_system", "os_version", "machine_architecture", "processor", "python_runtime", "hostname", "application_environment"):
        writer.writerow([key.replace("_", " ").title(), device.get(key, "Unavailable")])
    writer.writerow(["Collection timestamp", device["collected_at"].isoformat()])
    writer.writerow(["Scope", device["limitation"]])
    writer.writerow([])
    writer.writerow(["COLLECTED NETWORK FACTS"])
    for key in ("hostname", "local_ip", "default_gateway", "connectivity_status"):
        writer.writerow([key.replace("_", " ").title(), network.get(key, "Unavailable")])
    writer.writerow(["Interfaces", "; ".join(network.get("interfaces", [])) or "Unavailable"])
    writer.writerow(["DNS servers", "; ".join(network.get("dns_servers", [])) or "Unavailable"])
    writer.writerow(["Collection timestamp", network["collected_at"].isoformat()])
    writer.writerow(["Scope", network["limitation"]])
    writer.writerow([])
    writer.writerow(["SECURITY ACTIVITY SUMMARY"])
    writer.writerow(["Total recorded events", analytics["total_events"]])
    for label, count in analytics["tool_counts"].items():
        writer.writerow([label, count])
    writer.writerow([])
    writer.writerow(["RECOMMENDATIONS"])
    writer.writerow(["Classification", "Severity", "Title", "Reason"])
    for item in recommendations:
        writer.writerow([item["classification"], item["severity"], item["title"], item["reason"]])
    return output.getvalue().encode("utf-8")


def build_security_report_html(
    user_id: int,
    username: str,
    device: dict[str, object],
    network: dict[str, object],
    recommendations: list[dict[str, str]],
) -> str:
    analytics = get_analytics(user_id)
    generated = datetime.now(timezone.utc)
    tool_rows = "".join(
        f"<tr><td>{escape(label)}</td><td>{count}</td></tr>"
        for label, count in analytics["tool_counts"].items()
    )
    recommendation_rows = "".join(
        "<tr>"
        f"<td>{escape(item['classification'])}</td>"
        f"<td>{escape(item['severity'])}</td>"
        f"<td>{escape(item['title'])}</td>"
        f"<td>{escape(item['reason'])}</td>"
        "</tr>"
        for item in recommendations
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>CyberGuard Security Report</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;background:#080d18;color:#f8fafc;padding:32px}}main{{max-width:960px;margin:auto}}section{{border:1px solid #253248;border-radius:10px;padding:20px;margin:16px 0;background:#151f30}}table{{width:100%;border-collapse:collapse}}th,td{{border-bottom:1px solid #253248;padding:8px;text-align:left}}th{{color:#94a3b8}}small{{color:#94a3b8}}h1,h2{{color:#f8fafc}}</style>
</head><body><main>
<h1>CyberGuard Personal Security Intelligence Report</h1>
<small>Version {escape(current_app.config['APP_VERSION'])} | Generated {escape(generated.isoformat())} | Account {escape(username)}</small>
<p><strong>Scope:</strong> Collected facts and recommendations only; this is not a complete security audit.</p>
<section><h2>Collected device facts</h2><table><tr><th>Item</th><th>Value</th></tr>
<tr><td>Operating system</td><td>{escape(str(device.get('operating_system','Unavailable')))}</td></tr>
<tr><td>OS version</td><td>{escape(str(device.get('os_version','Unavailable')))}</td></tr>
<tr><td>Machine architecture</td><td>{escape(str(device.get('machine_architecture','Unavailable')))}</td></tr>
<tr><td>Processor</td><td>{escape(str(device.get('processor','Unavailable')))}</td></tr>
<tr><td>Python runtime</td><td>{escape(str(device.get('python_runtime','Unavailable')))}</td></tr>
<tr><td>Hostname</td><td>{escape(str(device.get('hostname','Unavailable')))}</td></tr>
<tr><td>Application environment</td><td>{escape(str(device.get('application_environment','Unavailable')))}</td></tr>
<tr><td>Collection timestamp</td><td>{escape(device['collected_at'].isoformat())}</td></tr>
</table><p><small>{escape(str(device['limitation']))}</small></p></section>
<section><h2>Collected network facts</h2><table><tr><th>Item</th><th>Value</th></tr>
<tr><td>Local hostname</td><td>{escape(str(network.get('hostname','Unavailable')))}</td></tr>
<tr><td>Local IP</td><td>{escape(str(network.get('local_ip','Unavailable')))}</td></tr>
<tr><td>Default gateway</td><td>{escape(str(network.get('default_gateway','Unavailable')))}</td></tr>
<tr><td>DNS servers</td><td>{escape('; '.join(network.get('dns_servers', [])) or 'Unavailable')}</td></tr>
<tr><td>Network interfaces</td><td>{escape('; '.join(network.get('interfaces', [])) or 'Unavailable')}</td></tr>
<tr><td>Connectivity status</td><td>{escape(str(network.get('connectivity_status','Unavailable')))}</td></tr>
</table><p><small>{escape(str(network['limitation']))}</small></p></section>
<section><h2>Security activity summary</h2><p><strong>Total recorded events:</strong> {analytics['total_events']}</p>
<table><tr><th>Tool usage</th><th>Count</th></tr>{tool_rows}</table></section>
<section><h2>Security recommendations</h2><table><tr><th>Classification</th><th>Severity</th><th>Title</th><th>Reason</th></tr>{recommendation_rows}</table></section>
</main></body></html>"""
