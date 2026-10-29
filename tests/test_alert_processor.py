
from unittest.mock import Mock, patch

from alert_processor import handle_alert


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


@patch("alert_processor.requests.post")
def test_alert_creates_incident(mock_post):
    mock_post.return_value = Mock(
        status_code=201,
        json=lambda: {
            "number": "INC100001",
            "state": "New",
        },
    )
    mock_post.return_value.raise_for_status.return_value = None

    result = handle_alert(sample_alert())

    assert result["processing_status"] == "incident_linked"
    assert result["incident_number"] == "INC100001"
    mock_post.assert_called_once()


@patch("alert_processor.requests.post")
def test_repeated_alert_uses_same_correlation_id(mock_post):
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {
            "number": "INC100001",
            "state": "New",
        },
    )
    mock_post.return_value.raise_for_status.return_value = None

    handle_alert(sample_alert())
    handle_alert(sample_alert())

    calls = mock_post.call_args_list
    first_payload = calls[0].kwargs["json"]
    second_payload = calls[1].kwargs["json"]

    assert (
        first_payload["correlation_id"]
        == second_payload["correlation_id"]
    )
