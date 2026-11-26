"""Active transport probing for TCP, TLS, and DNS consistency."""

from __future__ import annotations

import socket
import ssl
import time

from .metrics import LatencyStats, compute_stats


def probe_tcp_handshake(
    host: str,
    port: int,
    count: int = 5,
    timeout: float = 3.0,
) -> LatencyStats:
    """Measure TCP 3-way handshake RTT across multiple probes."""
    samples: list[float] = []
    errors: list[str] = []

    for _ in range(count):
        start = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=timeout):
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                samples.append(elapsed_ms)
        except (OSError, TimeoutError) as exc:
            errors.append(str(exc))

    detail = "TCP handshake OK" if samples else (errors[0] if errors else "Failed")
    return compute_stats(
        target=f"{host}:{port}",
        protocol="TCP",
        samples_ms=samples,
        total_attempts=count,
        detail=detail,
    )


def probe_tls_handshake(
    host: str,
    port: int = 443,
    count: int = 5,
    timeout: float = 4.0,
) -> LatencyStats:
    """Measure full TCP + TLS handshake latency and record negotiated TLS version."""
    samples: list[float] = []
    versions: set[str] = set()
    errors: list[str] = []
    ctx = ssl.create_default_context()

    for _ in range(count):
        start = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    elapsed_ms = (time.perf_counter() - start) * 1000.0
                    samples.append(elapsed_ms)
                    if ssock.version():
                        versions.add(ssock.version() or "Unknown")
        except (OSError, ssl.SSLError, TimeoutError) as exc:
            errors.append(str(exc))

    detail = f"Negotiated {', '.join(sorted(versions))}" if versions else (errors[0] if errors else "TLS failed")
    return compute_stats(
        target=f"{host}:{port}",
        protocol="TLS",
        samples_ms=samples,
        total_attempts=count,
        detail=detail,
    )


def probe_dns_consistency(
    hostname: str,
    count: int = 5,
    timeout: float = 3.0,
) -> LatencyStats:
    """Measure DNS resolution latency and verify IP answer consistency."""
    samples: list[float] = []
    ip_sets: list[tuple[str, ...]] = []
    errors: list[str] = []
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        for _ in range(count):
            start = time.perf_counter()
            try:
                infos = socket.getaddrinfo(hostname, None)
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                samples.append(elapsed_ms)
                ip_sets.append(tuple(sorted({info[4][0] for info in infos})))
            except socket.gaierror as exc:
                errors.append(str(exc))
    finally:
        socket.setdefaulttimeout(old_timeout)

    if ip_sets:
        unique_sets = set(ip_sets)
        detail = (
            f"Consistent ({', '.join(ip_sets[0])})"
            if len(unique_sets) == 1
            else f"Rotating/Inconsistent IPs ({len(unique_sets)} distinct sets)"
        )
    else:
        detail = errors[0] if errors else "DNS failed"

    return compute_stats(
        target=hostname,
        protocol="DNS",
        samples_ms=samples,
        total_attempts=count,
        detail=detail,
    )
