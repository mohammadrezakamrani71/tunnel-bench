# TunnelBench — Network Transport & Tunnel Performance Analyzer

**TunnelBench** is a zero-dependency Python CLI tool for measuring and comparing network transport and encrypted tunnel performance across endpoints—tracking **TCP/TLS handshake latency (Min / Avg / P95)**, **inter-probe jitter**, **packet-loss rate**, **DNS consistency**, and **MTU framing efficiency**.

## Key Features

- **Multi-Protocol Transport Probing (`tunnel_bench/prober.py`)**
  - **TCP Handshake RTT:** Measures 3-way handshake latency and connection drop rates across repeated probes.
  - **TLS Handshake & Version Inspection:** Measures full TCP + TLS setup latency and records negotiated TLS versions.
  - **DNS Resolution Consistency:** Tracks lookup latency and detects rotating or inconsistent DNS responses.
- **Statistical & MTU Analysis (`tunnel_bench/metrics.py`)**
  - Calculates `Min`, `Avg`, `P50`, `P95`, `Max` latency, inter-sample **jitter**, **packet-loss %**, and an overall link health rating (`EXCELLENT`, `GOOD`, `DEGRADED`, `POOR`).
  - Evaluates tunnel MTU vs. encapsulation overhead (e.g., IPsec, WireGuard, GRE, or QUIC) to compute usable payload bytes and framing efficiency.
- **Automated Reporting (`tunnel_bench/reporter.py`)**
  - Outputs structured **Markdown (`.md`)** and standalone **HTML (`.html`)** benchmark reports.

## Project Structure

```text
tunnel-bench/
├── main.py
├── tunnel_bench/
│   ├── __init__.py
│   ├── cli.py
│   ├── metrics.py
│   ├── prober.py
│   └── reporter.py
├── samples/
│   └── endpoints.json
├── tests/
│   └── test_tunnel_bench.py
├── LICENSE
└── README.md
```

## Quick Start

Requires **Python 3.10+** (pure standard library — zero external dependencies).

```bash
python3 main.py \
  --targets samples/endpoints.json \
  --count 5 \
  --out-md benchmark.md \
  --out-html benchmark.html
```

## Running Tests

```bash
python3 -m unittest discover -s tests -v
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
