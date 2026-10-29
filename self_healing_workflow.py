from typing import Any, Callable, Optional

from alert_engine import process_alert
from recovery_verifier import RecoveryVerificationError, verify_recovery
from remediation_engine import diagnose_alert, execute_remediation


def run_workflow(
    alert: dict[str, Any],
    *,
    recovery_verified: bool = False,
    provider: Optional[Callable[[dict[str, Any], str], Any]] = None,
    source: str = "simulated",
) -> dict[str, Any]:
    """Run a safe local POC workflow without modifying real resources.

    Recovery is decided in this order:
    1. recovery_verified=True  -> manual override (source "manual")
    2. otherwise the recovery verifier checks post-remediation observations
       - observation missing   -> awaiting_recovery_verification
       - issue still present   -> recovery_failed (incident stays open)
       - issue gone            -> recovery_verified (incident Resolved)
    """

    processed = process_alert(alert)
    diagnosis = diagnose_alert(processed)

    result = {
        "correlation_id": processed["correlation_id"],
        "alert_rule": processed["alert_rule"],
        "diagnosis": diagnosis["diagnosis"],
        "action": diagnosis["action"],
        "remediation": None,
        "recovery_verified": False,
        "recovery_source": None,
        "recovery_check": None,
        "incident_state": "New",
    }

    if diagnosis["action"] == "none":
        result["workflow_status"] = "manual_investigation_required"
        return result

    result["remediation"] = execute_remediation(
        diagnosis["action"],
        dry_run=True,
    )

    if recovery_verified:
        result["recovery_verified"] = True
        result["recovery_source"] = "manual"
        result["incident_state"] = "Resolved"
        result["workflow_status"] = "recovery_verified"
        return result

    verify_input = {**alert, "alert_rule": processed["alert_rule"]}
    try:
        check = verify_recovery(verify_input, provider=provider, source=source)
    except RecoveryVerificationError:
        check = None

    result["recovery_check"] = check

    if check is None or check["observed"] is None:
        result["workflow_status"] = "awaiting_recovery_verification"
    elif check["recovered"]:
        result["recovery_verified"] = True
        result["recovery_source"] = check["source"]
        result["incident_state"] = "Resolved"
        result["workflow_status"] = "recovery_verified"
    else:
        result["workflow_status"] = "recovery_failed"

    return result
