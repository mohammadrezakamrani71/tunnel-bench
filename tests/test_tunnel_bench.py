"""Unit tests for TunnelBench metrics, MTU calculations, probing, and reporting."""

import unittest

from tunnel_bench.metrics import compute_stats, estimate_mtu_efficiency
from tunnel_bench.prober import probe_dns_consistency
from tunnel_bench.reporter import render_html_report, render_markdown_report


class TestMetrics(unittest.TestCase):
    def test_compute_stats_with_loss_and_jitter(self) -> None:
        stats = compute_stats("10.0.0.1:443", "TCP", [10.0, 20.0, 15.0, 25.0], total_attempts=5)
        self.assertEqual(stats.successes, 4)
        self.assertEqual(stats.loss_pct, 20.0)
        self.assertEqual(stats.min_ms, 10.0)
        self.assertEqual(stats.max_ms, 25.0)
        self.assertEqual(stats.jitter_ms, 8.33)
        self.assertEqual(stats.rating, "DEGRADED")

    def test_compute_stats_all_failed(self) -> None:
        stats = compute_stats("10.0.0.9:443", "TLS", [], total_attempts=4)
        self.assertEqual(stats.loss_pct, 100.0)
        self.assertEqual(stats.rating, "POOR")
        self.assertIsNone(stats.avg_ms)

    def test_mtu_efficiency(self) -> None:
        rep = estimate_mtu_efficiency(1420, overhead_bytes=80)
        self.assertEqual(rep.payload_bytes, 1340)
        self.assertEqual(rep.efficiency_pct, 94.37)


class TestProberAndReporter(unittest.TestCase):
    def test_dns_localhost_consistency(self) -> None:
        res = probe_dns_consistency("localhost", count=3)
        self.assertEqual(res.loss_pct, 0.0)
        self.assertIn("Consistent", res.detail)

    def test_reports_render(self) -> None:
        stats = [compute_stats("localhost", "DNS", [1.0, 1.5], total_attempts=2, detail="Consistent")]
        mtu = [estimate_mtu_efficiency(1500, 40)]
        md = render_markdown_report(stats, mtu)
        html_out = render_html_report(stats, mtu)
        self.assertIn("TunnelBench Transport Performance Report", md)
        self.assertIn("<!DOCTYPE html>", html_out)


if __name__ == "__main__":
    unittest.main()
