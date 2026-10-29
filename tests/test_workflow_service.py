from unittest.mock import patch

from workflow_service import process_and_update_incident


def sample_alert():
    return {
        "alert_id": "workflow-service-001",
        "alert_rule": "Disk-Space-Low",
        "severity": "Sev2",
        "resource_id": "/subscriptions/demo/vm-demo",
        "description": "Disk capacity warning",
    }


@patch("workflow_service.requests.patch")
@patch("workflow_service.requests.post")
def test_workflow_creates_open_incident(mock_post, mock_patch):
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {
        "number": "INC100010",
        "state": "New",
    }
    mock_post.return_value.raise_for_status.return_value = None

    result = process_and_update_incident(sample_alert())

    assert result["incident_number"] == "INC100010"
    assert result["incident_state"] == "New"
    assert result["workflow_status"] == "awaiting_recovery_verification"
    mock_patch.assert_not_called()


@patch("workflow_service.requests.patch")
@patch("workflow_service.requests.post")
def test_verified_recovery_updates_incident(mock_post, mock_patch):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "number": "INC100010",
        "state": "New",
    }
    mock_post.return_value.raise_for_status.return_value = None

    mock_patch.return_value.status_code = 200
    mock_patch.return_value.json.return_value = {
        "number": "INC100010",
        "state": "Resolved",
    }
    mock_patch.return_value.raise_for_status.return_value = None

    result = process_and_update_incident(
        sample_alert(),
        recovery_verified=True,
    )

    assert result["incident_state"] == "Resolved"
    assert result["workflow_status"] == "recovery_verified"
    mock_patch.assert_called_once()
