"""Command-line interface for TunnelBench."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .metrics import LatencyStats, MtuReport, estimate_mtu_efficiency
from .prober import probe_dns_consistency, probe_tcp_handshake, probe_tls_handshake
from .reporter import render_html_report, render_markdown_report


def run_benchmark(targets_path: Path, count: int) -> tuple[list[LatencyStats], list[MtuReport]]:
    data = json.loads(targets_path.read_text(encoding="utf-8"))
    results: list[LatencyStats] = []

    for host in data.get("dns", []):
        results.append(probe_dns_consistency(host, count=count))

    for item in data.get("tcp", []):
        results.append(probe_tcp_handshake(item["host"], int(item["port"]), count=count))

    for item in data.get("tls", []):
        results.append(probe_tls_handshake(item["host"], int(item.get("port", 443)), count=count))

    mtu_reports = [
        estimate_mtu_efficiency(int(m["mtu"]), int(m.get("overhead", 40)))
        for m in data.get("mtu_profiles", [])
    ]
    return results, mtu_reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tunnel-bench",
        description="Network Transport & Tunnel Latency, Jitter, and Packet-Loss Analyzer",
    )
    parser.add_argument("--targets", type=Path, required=True, help="Path to endpoints JSON file")
    parser.add_argument("--count", type=int, default=5, help="Number of probes per endpoint (default: 5)")
    parser.add_argument("--out-md", type=Path, help="Optional Markdown report output path")
    parser.add_argument("--out-html", type=Path, help="Optional HTML report output path")
    args = parser.parse_args(argv)

    results, mtu_reports = run_benchmark(args.targets, count=args.count)
    md = render_markdown_report(results, mtu_reports)
    print(md)

    if args.out_md:
        args.out_md.write_text(md, encoding="utf-8")
    if args.out_html:
        args.out_html.write_text(render_html_report(results, mtu_reports), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
