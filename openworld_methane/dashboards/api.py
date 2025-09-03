from __future__ import annotations

from fastapi import FastAPI

from ..analytics.anomaly import detect_anomalies
from ..persistence.store import Store


def build_app(store: Store) -> FastAPI:
    app = FastAPI(title="OpenWorld Methane API")

    @app.get("/health")
    def health() -> dict[str, str]:  # pragma: no cover - runtime endpoint
        return {"status": "ok"}

    @app.get("/summary")
    def summary() -> dict[str, float | int]:  # pragma: no cover - runtime endpoint
        return store.summary()

    @app.get("/api/records")
    def get_records() -> list[dict[str, object]]:  # pragma: no cover - runtime endpoint
        return store.to_dicts()

    @app.get("/api/anomalies")
    def get_anomalies() -> list[dict[str, object]]:  # pragma: no cover - runtime endpoint
        payload: list[dict[str, object]] = []
        for a in detect_anomalies(store.all()):
            r = a.record
            payload.append(
                {
                    "timestamp": r.timestamp.isoformat(),
                    "site_id": r.site_id,
                    "region_id": r.region_id,
                    "rate_kg_h": r.emission_rate_kg_per_h,
                    "score": a.score,
                    "method": a.method,
                }
            )
        return payload

    return app
