from __future__ import annotations

from collections.abc import Iterable
from statistics import median

from ..models import Anomaly, EmissionRecord


def mad(values: list[float]) -> float:
    m = median(values)
    return median([abs(v - m) for v in values])


def robust_z_scores(values: list[float]) -> list[float]:
    if not values:
        return []
    m = median(values)
    mad_v = mad(values) or 1e-9
    return [0.6745 * (v - m) / mad_v for v in values]


def detect_anomalies(records: Iterable[EmissionRecord], z_threshold: float = 3.5) -> list[Anomaly]:
    records_list = list(records)
    values = [r.emission_rate_kg_per_h for r in records_list]
    zs = robust_z_scores(values)
    anomalies: list[Anomaly] = []
    for r, z in zip(records_list, zs):
        if abs(z) >= z_threshold:
            anomalies.append(Anomaly(record=r, score=z, method="robust_z", threshold=z_threshold))
    return anomalies


def seasonal_decompose_residuals(values: list[float], period: int) -> list[float]:
    if period <= 1 or period > len(values):
        return [v - (sum(values) / len(values) if values else 0.0) for v in values]
    # Compute mean per phase (position modulo period)
    phase_sums = [0.0] * period
    phase_counts = [0] * period
    for i, v in enumerate(values):
        p = i % period
        phase_sums[p] += v
        phase_counts[p] += 1
    phase_means = [phase_sums[i] / max(1, phase_counts[i]) for i in range(period)]
    # Remove seasonal means
    residuals = [v - phase_means[i % period] for i, v in enumerate(values)]
    return residuals


def detect_anomalies_seasonal(
    records: Iterable[EmissionRecord], period: int = 24, z_threshold: float = 3.5
) -> list[Anomaly]:
    records_list = list(records)
    values = [r.emission_rate_kg_per_h for r in records_list]
    residuals = seasonal_decompose_residuals(values, period)
    zs = robust_z_scores(residuals)
    anomalies: list[Anomaly] = []
    for r, z in zip(records_list, zs):
        if abs(z) >= z_threshold:
            anomalies.append(
                Anomaly(
                    record=r, score=z, method=f"seasonal(period={period})", threshold=z_threshold
                )
            )
    return anomalies
