
import requests

from alert_engine import process_alert


SERVICENOW_URL = "http://127.0.0.1:8090"


def handle_alert(alert: dict) -> dict:
    """Validate an alert and create or reuse its mock incident."""

    processed = process_alert(alert)

    payload = {
        "correlation_id": processed["correlation_id"],
        "short_description": (
            f"[{processed['severity']}] "
            f"{processed['alert_rule']}: "
            f"{processed['description']}"
        ),
    }

    response = requests.post(
        f"{SERVICENOW_URL}/api/incidents",
        json=payload,
        timeout=5,
    )
    response.raise_for_status()

    incident = response.json()

    return {
        "processing_status": "incident_linked",
        "correlation_id": processed["correlation_id"],
        "incident_number": incident["number"],
        "incident_state": incident["state"],
    }
