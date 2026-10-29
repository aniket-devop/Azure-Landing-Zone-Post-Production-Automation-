
import pytest

from alert_engine import (
    AlertValidationError,
    create_correlation_id,
    process_alert,
    validate_alert,
)


@pytest.fixture
def sample_alert():
    return {
        "alert_id": "alert-001",
        "alert_rule": "VM-Heartbeat-Failure",
        "severity": "Sev2",
        "resource_id": (
            "/subscriptions/demo/resourceGroups/rg-lab/"
            "providers/Microsoft.Compute/virtualMachines/vm-demo"
        ),
        "description": "VM heartbeat is missing",
    }


def test_valid_alert_is_processed(sample_alert):
    result = process_alert(sample_alert)

    assert result["processing_status"] == "validated"
    assert result["severity"] == "Sev2"
    assert result["correlation_id"].startswith("IYAV-")


def test_same_resource_and_rule_have_same_correlation_id(sample_alert):
    first = process_alert(sample_alert)
    second = process_alert(sample_alert.copy())

    assert first["correlation_id"] == second["correlation_id"]


def test_different_resource_has_different_correlation_id(sample_alert):
    first = process_alert(sample_alert)

    changed = sample_alert.copy()
    changed["resource_id"] = "/subscriptions/demo/vm-other"

    second = process_alert(changed)

    assert first["correlation_id"] != second["correlation_id"]


def test_invalid_severity_is_rejected(sample_alert):
    sample_alert["severity"] = "Critical"

    with pytest.raises(AlertValidationError):
        validate_alert(sample_alert)


def test_missing_resource_id_is_rejected(sample_alert):
    del sample_alert["resource_id"]

    with pytest.raises(AlertValidationError):
        validate_alert(sample_alert)
