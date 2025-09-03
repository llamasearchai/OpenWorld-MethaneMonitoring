from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from ..models import EmissionRecord, Remediation


@dataclass(frozen=True)
class ThresholdRule:
    rule_id: str
    threshold_kg_per_h: float
    due_days: int


def evaluate_threshold_rule(
    records: Iterable[EmissionRecord], rule: ThresholdRule
) -> list[Remediation]:
    remediations: list[Remediation] = []
    for r in records:
        if r.emission_rate_kg_per_h >= rule.threshold_kg_per_h:
            detected = r.timestamp
            due = detected + timedelta(days=rule.due_days)
            status = "overdue" if due < datetime.now(tz=timezone.utc) else "open"
            remediations.append(
                Remediation(
                    site_id=r.site_id,
                    region_id=r.region_id,
                    detected_at=detected,
                    due_by=due,
                    status=status,
                    rule_id=rule.rule_id,
                    details=(
                        f"Emission {r.emission_rate_kg_per_h:.3f} kg/h exceeds "
                        f"threshold {rule.threshold_kg_per_h:.3f} kg/h"
                    ),
                )
            )
    return remediations


def load_rules_from_dict(data: Any) -> list[ThresholdRule]:
    rules: list[ThresholdRule] = []
    if not isinstance(data, list):
        raise ValueError("Rules must be a list")
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Rule must be an object")
        if item.get("type", "threshold") != "threshold":
            continue
        rules.append(
            ThresholdRule(
                rule_id=str(item.get("id", "T1")),
                threshold_kg_per_h=float(item["threshold_kg_per_h"]),
                due_days=int(item.get("due_days", 7)),
            )
        )
    return rules


def load_rules(path: str) -> list[ThresholdRule]:
    if path.lower().endswith((".yaml", ".yml")):
        try:
            import yaml  # type: ignore
        except Exception as e:  # noqa: BLE001
            raise RuntimeError("PyYAML is required to load YAML rules") from e
        with open(path, encoding="utf-8") as fp:
            data = yaml.safe_load(fp)
            return load_rules_from_dict(data)
    else:
        import json

        with open(path, encoding="utf-8") as fp:
            data = json.load(fp)
            return load_rules_from_dict(data)
