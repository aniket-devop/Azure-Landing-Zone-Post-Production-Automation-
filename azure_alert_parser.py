"""Azure Monitor Common Alert Schema parser for IYAV.

Converts a Common Alert Schema payload into the internal alert dict:
{alert_id, alert_rule, severity, resource_id, description}

Field names follow the documented schema (data.essentials). They are
checked against sample payloads in tests, not against live Azure.
"""
from typing import Any, Dict


class AlertSchemaError(ValueError):
    """Raised when a payload is not a valid Common Alert Schema alert."""


def _require(essentials: Dict[str, Any], key: str) -> Any:
    value = essentials.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise AlertSchemaError(f"Missing required field: data.essentials.{key}")
    return value


def parse_common_alert(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise AlertSchemaError("Payload must be a JSON object")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise AlertSchemaError("Missing required field: data")

    essentials = data.get("essentials")
    if not isinstance(essentials, dict):
        raise AlertSchemaError("Missing required field: data.essentials")

    targets = _require(essentials, "alertTargetIDs")
    if not isinstance(targets, list) or not targets:
        raise AlertSchemaError("data.essentials.alertTargetIDs must be a non-empty list")

    return {
        "alert_id": str(_require(essentials, "alertId")),
        "alert_rule": str(_require(essentials, "alertRule")),
        "severity": str(_require(essentials, "severity")),
        "resource_id": str(targets[0]),
        "description": str(essentials.get("description") or ""),
    }
