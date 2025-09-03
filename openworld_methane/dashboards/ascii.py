from __future__ import annotations

from collections.abc import Iterable

from ..models import EmissionRecord


def _sparkline(values: list[float]) -> str:
    # Simple ASCII sparkline using characters: .:-=+*#%
    if not values:
        return ""
    blocks = ".:-=+*#%"
    mn = min(values)
    mx = max(values)
    span = mx - mn or 1e-9
    chars = []
    for v in values:
        idx = int((v - mn) / span * (len(blocks) - 1))
        chars.append(blocks[idx])
    return "".join(chars)


def render_dashboard(records: Iterable[EmissionRecord]) -> str:
    data = list(records)
    vals = [r.emission_rate_kg_per_h for r in data]
    s = []
    s.append("OpenWorld Methane Dashboard")
    s.append("============================")
    if not data:
        s.append("No data.")
        return "\n".join(s)
    s.append(
        f"Records: {len(data)}  Mean: {sum(vals)/len(vals):.3f} kg/h  Min: {min(vals):.3f}  Max: {max(vals):.3f}"
    )
    s.append(f"Sparkline: {_sparkline(vals)}")
    s.append("")
    s.append("By site:")
    by_site: dict[str, list[float]] = {}
    for r in data:
        by_site.setdefault(r.site_id, []).append(r.emission_rate_kg_per_h)
    for site, vs in sorted(by_site.items()):
        s.append(f"  {site:10s} mean={sum(vs)/len(vs):.3f} kg/h  { _sparkline(vs)}")
    return "\n".join(s)
