from self_healing_workflow import run_workflow


def sample_alert():
    return {
        "alert_id": "workflow-001",
        "alert_rule": "Disk-Space-Low",
        "severity": "Sev2",
        "resource_id": "/subscriptions/demo/vm-demo",
        "description": "Disk capacity warning",
    }


def test_workflow_waits_for_recovery_verification():
    result = run_workflow(sample_alert())

    assert result["workflow_status"] == "awaiting_recovery_verification"
    assert result["incident_state"] == "New"
    assert result["remediation"]["resource_changed"] is False


def test_workflow_resolves_only_when_verification_is_supplied():
    result = run_workflow(sample_alert(), recovery_verified=True)

    assert result["workflow_status"] == "recovery_verified"
    assert result["incident_state"] == "Resolved"


def test_unknown_alert_is_sent_for_manual_investigation():
    alert = sample_alert()
    alert["alert_rule"] = "Unknown-Alert"

    result = run_workflow(alert)

    assert result["workflow_status"] == "manual_investigation_required"
    assert result["remediation"] is None
