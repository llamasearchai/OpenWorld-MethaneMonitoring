from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional  # noqa: F401

from ..analytics.anomaly import detect_anomalies
from ..dashboards.ascii import render_dashboard
from ..persistence.store import DataStore


def render_html(store: DataStore) -> str:
    recs = store.tail(200)
    dash = render_dashboard(recs)
    s = []
    s.append("<!doctype html><html><head><meta charset='utf-8'><title>OpenWorld Methane</title>")
    s.append(
        "<style>body{font-family:system-ui, sans-serif;padding:1rem} "
        "pre{background:#f6f8fa;padding:1rem;white-space:pre-wrap} "
        "table{border-collapse:collapse} td,th{border:1px solid #ddd;padding:4px 8px}</style>"
    )
    s.append("</head><body>")
    s.append("<h1>OpenWorld Methane</h1>")
    sm = store.summary()
    s.append(
        f"<p>Records: {sm['count']} &middot; Mean: {sm['mean']:.3f} kg/h "
        f"&middot; Min: {sm['min']:.3f} &middot; Max: {sm['max']:.3f}</p>"
    )
    s.append("<h2>Dashboard</h2><pre>")
    s.append(dash)
    s.append("</pre>")
    # show last 10 records in table
    s.append("<h2>Recent Records</h2>")
    s.append(
        "<table><thead><tr><th>Timestamp</th><th>Site</th><th>Region</th><th>kg/h</th></tr></thead><tbody>"
    )
    for r in recs[-10:]:
        s.append(
            f"<tr><td>{r.timestamp.isoformat()}</td><td>{r.site_id}</td>"
            f"<td>{r.region_id}</td><td>{r.emission_rate_kg_per_h:.3f}</td></tr>"
        )
    s.append("</tbody></table>")
    s.append("</body></html>")
    return "".join(s)


class DashboardHandler(BaseHTTPRequestHandler):
    def __init__(self, store: DataStore, *args, **kwargs):
        self.store = store
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        store = self.store

        if self.path == "/" or self.path.startswith("/index"):
            body = render_html(store).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/api/records":
            data = json.dumps(store.to_dicts()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if self.path == "/api/anomalies":
            anomalies = detect_anomalies(store.all())
            payload = []
            for a in anomalies:
                r = a.record
                payload.append(
                    {
                        "timestamp": r.timestamp.isoformat(),
                        "site_id": r.site_id,
                        "region_id": r.region_id,
                        "rate_kg_h": r.emission_rate_kg_per_h,
                        "z": a.score,
                    }
                )
            data = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not found")


def serve_http(store: DataStore, host: str = "127.0.0.1", port: int = 8000) -> None:
    def handler_factory(*args, **kwargs):
        return DashboardHandler(store, *args, **kwargs)

    httpd = HTTPServer((host, port), handler_factory)
    print(f"Serving dashboard on http://{host}:{port}")
    httpd.serve_forever()
