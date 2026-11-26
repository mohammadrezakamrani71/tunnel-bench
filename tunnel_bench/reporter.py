"""Markdown and HTML benchmark report generator for TunnelBench."""

from __future__ import annotations

import html
from datetime import datetime, timezone

from .metrics import LatencyStats, MtuReport


def _fmt(val: float | None) -> str:
    return f"{val:.2f}" if val is not None else "-"


def render_markdown_report(
    results: list[LatencyStats],
    mtu_reports: list[MtuReport] | None = None,
    title: str = "TunnelBench Transport Performance Report",
) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# {title}",
        "",
        f"**Generated:** {timestamp}",
        "",
    ]

    if results:
        lines.extend(
            [
                "## 1. Endpoint Latency, Jitter & Packet-Loss Summary",
                "",
                "| Target | Protocol | Loss (%) | Min (ms) | Avg (ms) | P95 (ms) | Jitter (ms) | Rating | Detail |",
                "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- |",
            ]
        )
        for r in results:
            lines.append(
                f"| `{r.target}` | {r.protocol} | {r.loss_pct:.1f}% | {_fmt(r.min_ms)} | {_fmt(r.avg_ms)} | "
                f"{_fmt(r.p95_ms)} | {_fmt(r.jitter_ms)} | **{r.rating}** | {r.detail} |"
            )
        lines.append("")

    if mtu_reports:
        lines.extend(
            [
                "## 2. Tunnel MTU & Payload Efficiency",
                "",
                "| MTU (bytes) | Tunnel Overhead (bytes) | Usable Payload (bytes) | Efficiency (%) |",
                "| ---: | ---: | ---: | ---: |",
            ]
        )
        for m in mtu_reports:
            lines.append(f"| {m.mtu} | {m.overhead_bytes} | {m.payload_bytes} | {m.efficiency_pct:.2f}% |")
        lines.append("")

    return "\n".join(lines)


def render_html_report(
    results: list[LatencyStats],
    mtu_reports: list[MtuReport] | None = None,
    title: str = "TunnelBench Transport Performance Report",
) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def badge(rating: str) -> str:
        colors = {
            "EXCELLENT": "#16a34a",
            "GOOD": "#2563eb",
            "DEGRADED": "#d97706",
            "POOR": "#dc2626",
        }
        bg = colors.get(rating, "#475569")
        return f'<span style="background:{bg};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600;">{html.escape(rating)}</span>'

    rows = "\n".join(
        f"<tr><td><code>{html.escape(r.target)}</code></td><td>{html.escape(r.protocol)}</td>"
        f"<td>{r.loss_pct:.1f}%</td><td>{_fmt(r.min_ms)}</td><td>{_fmt(r.avg_ms)}</td>"
        f"<td>{_fmt(r.p95_ms)}</td><td>{_fmt(r.jitter_ms)}</td><td>{badge(r.rating)}</td>"
        f"<td>{html.escape(r.detail)}</td></tr>"
        for r in results
    )

    mtu_rows = "\n".join(
        f"<tr><td>{m.mtu}</td><td>{m.overhead_bytes}</td><td>{m.payload_bytes}</td><td>{m.efficiency_pct:.2f}%</td></tr>"
        for m in (mtu_reports or [])
    )

    mtu_section = (
        f"<h2>Tunnel MTU &amp; Payload Efficiency</h2>"
        f"<table><thead><tr><th>MTU (bytes)</th><th>Overhead (bytes)</th><th>Payload (bytes)</th><th>Efficiency (%)</th></tr></thead>"
        f"<tbody>{mtu_rows}</tbody></table>"
        if mtu_reports
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 32px; background: #f8fafc; color: #0f172a; }}
  .container {{ max-width: 1120px; margin: 0 auto; background: #fff; padding: 28px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }}
  h1 {{ margin-top: 0; font-size: 24px; }}
  .meta {{ color: #475569; font-size: 14px; margin-bottom: 22px; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 28px; font-size: 14px; }}
  th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid #e2e8f0; }}
  th {{ background: #f1f5f9; font-weight: 600; }}
  code {{ background: #f1f5f9; padding: 2px 5px; border-radius: 4px; font-size: 13px; }}
</style>
</head>
<body>
<div class="container">
  <h1>{html.escape(title)}</h1>
  <div class="meta">Generated: {html.escape(timestamp)}</div>
  <h2>Endpoint Latency, Jitter &amp; Packet-Loss Summary</h2>
  <table>
    <thead><tr><th>Target</th><th>Protocol</th><th>Loss</th><th>Min (ms)</th><th>Avg (ms)</th><th>P95 (ms)</th><th>Jitter (ms)</th><th>Rating</th><th>Detail</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  {mtu_section}
</div>
</body>
</html>
"""
