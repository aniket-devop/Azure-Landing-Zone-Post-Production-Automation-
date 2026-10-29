import copy

import pytest

from azure_alert_parser import AlertSchemaError, parse_common_alert


SAMPLE = {
    "schemaId": "azureMonitorCommonAlertSchema",
    "data": {
        "essentials": {
            "alertId": "/subscriptions/demo/providers/Microsoft.AlertsManagement/alerts/abc123",
            "alertRule": "Disk-Space-Low",
            "severity": "Sev2",
            "signalType": "Metric",
            "monitorCondition": "Fired",
            "alertTargetIDs": [
                "/subscriptions/demo/resourceGroups/rg-lab/providers/Microsoft.Compute/virtualMachines/vm-demo"
            ],
            "description": "Disk capacity warning detected",
        },
        "alertContext": {},
    },
}


def test_parses_valid_payload():
    alert = parse_common_alert(SAMPLE)
    assert alert["alert_rule"] == "Disk-Space-Low"
    assert alert["severity"] == "Sev2"
    assert alert["resource_id"].endswith("virtualMachines/vm-demo")
    assert alert["alert_id"].endswith("abc123")
    assert alert["description"] == "Disk capacity warning detected"


def test_uses_first_target_when_multiple():
    payload = copy.deepcopy(SAMPLE)
    payload["data"]["essentials"]["alertTargetIDs"] = ["/res/one", "/res/two"]
    assert parse_common_alert(payload)["resource_id"] == "/res/one"


def test_missing_description_becomes_empty_string():
    payload = copy.deepcopy(SAMPLE)
    del payload["data"]["essentials"]["description"]
    assert parse_common_alert(payload)["description"] == ""


@pytest.mark.parametrize("field", ["alertId", "alertRule", "severity", "alertTargetIDs"])
def test_missing_required_field_raises(field):
    payload = copy.deepcopy(SAMPLE)
    del payload["data"]["essentials"][field]
    with pytest.raises(AlertSchemaError):
        parse_common_alert(payload)


def test_empty_target_list_raises():
    payload = copy.deepcopy(SAMPLE)
    payload["data"]["essentials"]["alertTargetIDs"] = []
    with pytest.raises(AlertSchemaError):
        parse_common_alert(payload)


def test_missing_data_raises():
    with pytest.raises(AlertSchemaError):
        parse_common_alert({"schemaId": "azureMonitorCommonAlertSchema"})


def test_non_dict_payload_raises():
    with pytest.raises(AlertSchemaError):
        parse_common_alert("not a dict")


def test_parsed_alert_runs_through_workflow():
    from self_healing_workflow import run_workflow

    alert = parse_common_alert(SAMPLE)
    result = run_workflow(alert)
    assert result["alert_rule"] == "Disk-Space-Low"
    assert result["workflow_status"] == "awaiting_recovery_verification"
