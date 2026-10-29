import requests

from self_healing_workflow import run_workflow


SERVICENOW_URL = "http://127.0.0.1:8090"


def process_and_update_incident(
    alert: dict,
    *,
    recovery_verified: bool = False,
) -> dict:
    workflow = run_workflow(
        alert,
        recovery_verified=recovery_verified,
    )

    payload = {
        "correlation_id": workflow["correlation_id"],
        "short_description": (
            f"[{alert['severity']}] "
            f"{workflow['alert_rule']}: {alert['description']}"
        ),
    }

    response = requests.post(
        f"{SERVICENOW_URL}/api/incidents",
        json=payload,
        timeout=5,
    )
    response.raise_for_status()
    incident = response.json()

    if workflow["incident_state"] == "Resolved":
        update_response = requests.patch(
            f"{SERVICENOW_URL}/api/incidents/{incident['number']}",
            json={
                "state": "Resolved",
                "recovery_verified": True,
            },
            timeout=5,
        )
        update_response.raise_for_status()
        incident = update_response.json()

    return {
        "workflow_status": workflow["workflow_status"],
        "correlation_id": workflow["correlation_id"],
        "incident_number": incident["number"],
        "incident_state": incident["state"],
        "remediation": workflow["remediation"],
    }
