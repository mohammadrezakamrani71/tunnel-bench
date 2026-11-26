"""Statistical metrics and MTU efficiency calculations for network transport benchmarking."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class LatencyStats:
    target: str
    protocol: str
    attempts: int
    successes: int
    loss_pct: float
    min_ms: float | None
    avg_ms: float | None
    p50_ms: float | None
    p95_ms: float | None
    max_ms: float | None
    jitter_ms: float | None
    rating: str
    detail: str = ""


@dataclass
class MtuReport:
    mtu: int
    overhead_bytes: int
    payload_bytes: int
    efficiency_pct: float


def _percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def compute_stats(
    target: str,
    protocol: str,
    samples_ms: list[float],
    total_attempts: int,
    detail: str = "",
) -> LatencyStats:
    """Compute latency percentiles, RFC-style inter-sample jitter, and packet loss percentage."""
    if total_attempts <= 0:
        raise ValueError("total_attempts must be positive")

    successes = len(samples_ms)
    loss_pct = round(((total_attempts - successes) / total_attempts) * 100.0, 2)

    if not samples_ms:
        return LatencyStats(
            target=target,
            protocol=protocol,
            attempts=total_attempts,
            successes=0,
            loss_pct=100.0,
            min_ms=None,
            avg_ms=None,
            p50_ms=None,
            p95_ms=None,
            max_ms=None,
            jitter_ms=None,
            rating="POOR",
            detail=detail or "All probes timed out or failed",
        )

    ordered = sorted(samples_ms)
    min_ms = round(ordered[0], 2)
    max_ms = round(ordered[-1], 2)
    avg_ms = round(sum(ordered) / len(ordered), 2)
    p50_ms = round(_percentile(ordered, 50), 2)
    p95_ms = round(_percentile(ordered, 95), 2)

    if len(samples_ms) >= 2:
        deltas = [abs(samples_ms[i] - samples_ms[i - 1]) for i in range(1, len(samples_ms))]
        jitter_ms = round(sum(deltas) / len(deltas), 2)
    else:
        jitter_ms = 0.0

    if loss_pct > 20.0 or p95_ms > 400.0:
        rating = "POOR"
    elif loss_pct > 5.0 or p95_ms > 200.0 or jitter_ms > 40.0:
        rating = "DEGRADED"
    elif p95_ms > 80.0 or jitter_ms > 15.0:
        rating = "GOOD"
    else:
        rating = "EXCELLENT"

    return LatencyStats(
        target=target,
        protocol=protocol,
        attempts=total_attempts,
        successes=successes,
        loss_pct=loss_pct,
        min_ms=min_ms,
        avg_ms=avg_ms,
        p50_ms=p50_ms,
        p95_ms=p95_ms,
        max_ms=max_ms,
        jitter_ms=jitter_ms,
        rating=rating,
        detail=detail,
    )


def estimate_mtu_efficiency(mtu: int, overhead_bytes: int = 40) -> MtuReport:
    """Calculate payload bytes and framing efficiency for a given MTU and tunnel overhead."""
    if mtu <= overhead_bytes:
        raise ValueError("MTU must be greater than overhead_bytes")
    payload = mtu - overhead_bytes
    efficiency = round((payload / mtu) * 100.0, 2)
    return MtuReport(
        mtu=mtu,
        overhead_bytes=overhead_bytes,
        payload_bytes=payload,
        efficiency_pct=efficiency,
    )
