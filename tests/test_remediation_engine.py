import pytest

from remediation_engine import (
    RemediationError,
    diagnose_alert,
    execute_remediation,
)


def test_disk_alert_maps_to_approved_action():
    result = diagnose_alert({"alert_rule": "Disk-Space-Low"})

    assert result["diagnosis"] == "known_issue"
    assert result["action"] == "clear_temp_files"


def test_unknown_alert_requires_manual_investigation():
    result = diagnose_alert({"alert_rule": "Unknown-Alert"})

    assert result["diagnosis"] == "manual_investigation_required"
    assert result["action"] == "none"


def test_approved_action_is_simulated():
    result = execute_remediation("restart_app")

    assert result["status"] == "simulated"
    assert result["resource_changed"] is False


def test_unapproved_action_is_rejected():
    with pytest.raises(RemediationError):
        execute_remediation("delete_production_vm")
