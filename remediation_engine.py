from typing import Any

from rules import RULES


APPROVED_ACTIONS = {rule["action"] for rule in RULES.values()}


class RemediationError(ValueError):
    """Raised when a remediation action is not approved."""


def diagnose_alert(alert: dict[str, Any]) -> dict[str, str]:
    """Map a known alert rule to an approved remediation action."""

    rule = RULES.get(alert.get("alert_rule"))

    if rule is None:
        return {
            "diagnosis": "manual_investigation_required",
            "action": "none",
        }

    return {
        "diagnosis": "known_issue",
        "action": rule["action"],
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
