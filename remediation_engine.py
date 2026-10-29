
from typing import Any


APPROVED_ACTIONS = {
    "clear_temp_files",
    "restart_app",
    "retry_backup",
}


class RemediationError(ValueError):
    """Raised when a remediation action is not approved."""


def diagnose_alert(alert: dict[str, Any]) -> dict[str, str]:
    """Map a known alert rule to an approved remediation action."""

    rule = alert.get("alert_rule")

    action_by_rule = {
        "Disk-Space-Low": "clear_temp_files",
        "Application-Health-Failure": "restart_app",
        "Backup-Job-Failure": "retry_backup",
    }

    action = action_by_rule.get(rule)

    if action is None:
        return {
            "diagnosis": "manual_investigation_required",
            "action": "none",
        }

    return {
        "diagnosis": "known_issue",
        "action": action,
    }


def execute_remediation(
    action: str,
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Validate and simulate an approved action; never change real resources."""

    if action not in APPROVED_ACTIONS:
        raise RemediationError(f"Action is not approved: {action}")

    return {
        "action": action,
        "status": "simulated",
        "dry_run": dry_run,
        "resource_changed": False,
        "message": "No real resource was modified.",
    }
