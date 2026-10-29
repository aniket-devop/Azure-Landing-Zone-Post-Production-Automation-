from self_healing_workflow import run_workflow


def _disk_alert(**extra):
    alert = {
        "alert_id": "IYAV-TEST-DISK-001",
        "alert_rule": "Disk-Space-Low",
        "severity": "Sev2",
        "resource_id": "/subscriptions/demo/resourceGroups/rg-lab/providers/Microsoft.Compute/virtualMachines/vm-demo",
        "description": "Disk capacity warning detected",
    }
    alert.update(extra)
    return alert


def test_recovered_via_post_remediation_state():
    alert = _disk_alert(post_remediation_state={"disk_free_percent": 35})
    result = run_workflow(alert)
    assert result["workflow_status"] == "recovery_verified"
    assert result["recovery_verified"] is True
    assert result["recovery_source"] == "simulated"
    assert result["incident_state"] == "Resolved"
    assert result["recovery_check"]["recovered"] is True


def test_recovery_failed_when_issue_still_present():
    alert = _disk_alert(post_remediation_state={"disk_free_percent": 5})
    result = run_workflow(alert)
    assert result["workflow_status"] == "recovery_failed"
    assert result["recovery_verified"] is False
    assert result["incident_state"] == "New"
    assert result["recovery_check"]["recovered"] is False


def test_recovered_via_custom_provider():
    alert = _disk_alert()
    result = run_workflow(
        alert,
        provider=lambda a, check: 50,
        source="test-provider",
    )
    assert result["workflow_status"] == "recovery_verified"
    assert result["recovery_source"] == "test-provider"
    assert result["incident_state"] == "Resolved"


def test_manual_override_beats_failed_observation():
    alert = _disk_alert(post_remediation_state={"disk_free_percent": 5})
    result = run_workflow(alert, recovery_verified=True)
    assert result["workflow_status"] == "recovery_verified"
    assert result["recovery_source"] == "manual"
    assert result["incident_state"] == "Resolved"
