
import hashlib
from typing import Any


VALID_SEVERITIES = {"Sev0", "Sev1", "Sev2", "Sev3", "Sev4"}


class AlertValidationError(ValueError):
    """Raised when an incoming monitoring alert is invalid."""


def validate_alert(alert: dict[str, Any]) -> dict[str, str]:
    """Validate and normalize a simulated Azure Monitor alert."""

    if not isinstance(alert, dict):
        raise AlertValidationError("Alert must be a JSON object")

    required_fields = [
        "alert_id",
        "alert_rule",
        "severity",
        "resource_id",
        "description",
    ]

    normalized = {}

    for field in required_fields:
        value = alert.get(field)

        if not isinstance(value, str) or not value.strip():
            raise AlertValidationError(
                f"Missing or invalid field: {field}"
            )

        normalized[field] = value.strip()

    if normalized["severity"] not in VALID_SEVERITIES:
        raise AlertValidationError(
            "severity must be Sev0, Sev1, Sev2, Sev3, or Sev4"
        )

    normalized["resource_id"] = normalized["resource_id"].lower()

    return normalized


def create_correlation_id(alert: dict[str, str]) -> str:
    """Create a stable fingerprint for the same resource and alert rule."""

    resource_id = alert["resource_id"].strip().lower()
    alert_rule = alert["alert_rule"].strip().lower()

    fingerprint = f"{resource_id}|{alert_rule}"

    digest = hashlib.sha256(
        fingerprint.encode("utf-8")
    ).hexdigest()[:16]

    return f"IYAV-{digest.upper()}"


def process_alert(alert: dict[str, Any]) -> dict[str, str]:
    """Validate an alert and prepare it for incident management."""

    normalized = validate_alert(alert)

    return {
        **normalized,
        "correlation_id": create_correlation_id(normalized),
        "processing_status": "validated",
    }
