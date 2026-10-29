import pytest

from recovery_verifier import RecoveryVerificationError, verify_recovery


def test_disk_recovered():
    alert = {"alert_rule": "Disk-Space-Low", "post_remediation_state": {"disk_free_percent": 42}}
    result = verify_recovery(alert)
    assert result["recovered"] is True
    assert result["source"] == "simulated"


def test_disk_still_low():
    alert = {"alert_rule": "Disk-Space-Low", "post_remediation_state": {"disk_free_percent": 8}}
    assert verify_recovery(alert)["recovered"] is False


def test_app_health_recovered():
    alert = {"alert_rule": "Application-Health-Failure", "post_remediation_state": {"app_health_status": "Healthy"}}
    assert verify_recovery(alert)["recovered"] is True


def test_backup_failed_again():
    alert = {"alert_rule": "Backup-Job-Failure", "post_remediation_state": {"last_backup_status": "Failed"}}
    assert verify_recovery(alert)["recovered"] is False


def test_missing_observation_is_not_recovered():
    result = verify_recovery({"alert_rule": "Disk-Space-Low"})
    assert result["recovered"] is False
    assert result["observed"] is None


def test_unknown_rule_raises():
    with pytest.raises(RecoveryVerificationError):
        verify_recovery({"alert_rule": "Something-Else"})


def test_custom_provider_is_used():
    alert = {"alert_rule": "Disk-Space-Low"}
    result = verify_recovery(alert, provider=lambda a, c: 55, source="fake")
    assert result["recovered"] is True
    assert result["source"] == "fake"
