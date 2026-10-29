"""Recovery verification for IYAV.

Checks whether an alert's underlying issue is actually resolved after
remediation. Observations come from a pluggable provider. The default
provider reads simulated data from the alert payload, so results are
labelled source="simulated" until a real Azure provider is added.
"""
from typing import Any, Callable, Dict, Optional


class RecoveryVerificationError(Exception):
    """Raised when recovery cannot be verified for an unsupported alert rule."""


RECOVERY_CHECKS: Dict[str, Dict[str, Any]] = {
    "Disk-Space-Low": {
        "check": "disk_free_percent",
        "mode": "min",
        "threshold": 20,
    },
    "Application-Health-Failure": {
        "check": "app_health_status",
        "mode": "equals",
        "expected": "Healthy",
    },
    "Backup-Job-Failure": {
        "check": "last_backup_status",
        "mode": "equals",
        "expected": "Succeeded",
    },
}

Provider = Callable[[Dict[str, Any], str], Optional[Any]]


def simulated_provider(alert: Dict[str, Any], check_name: str) -> Optional[Any]:
    """Read a post-remediation observation from the alert payload (simulated)."""
    state = alert.get("post_remediation_state") or {}
    return state.get(check_name)


def verify_recovery(
    alert: Dict[str, Any],
    provider: Optional[Provider] = None,
    source: str = "simulated",
) -> Dict[str, Any]:
    rule = alert.get("alert_rule")
    spec = RECOVERY_CHECKS.get(rule)
    if spec is None:
        raise RecoveryVerificationError(f"No recovery check defined for rule: {rule}")

    provider = provider or simulated_provider
    check_name = spec["check"]
    observed = provider(alert, check_name)

    result: Dict[str, Any] = {
        "recovered": False,
        "rule": rule,
        "check": check_name,
        "observed": observed,
        "source": source,
    }

    if observed is None:
        result["message"] = "No observation available; recovery not verified."
        return result

    if spec["mode"] == "min":
        result["threshold"] = spec["threshold"]
        result["recovered"] = observed >= spec["threshold"]
    else:
        result["expected"] = spec["expected"]
        result["recovered"] = observed == spec["expected"]

    result["message"] = (
        "Recovery verified." if result["recovered"] else "Issue still present."
    )
    return result
