"""Run every scenario in rules.py through the workflow and the mock ServiceNow.

Needs the mock server running: python mock_servicenow.py
All remediation is dry-run; observations are simulated.
"""
import sys
import time

import requests

from rules import RULES
from workflow_service import process_and_update_incident

GOOD = {
    "equals": lambda spec: spec["expected"],
    "min": lambda spec: spec["threshold"] + 1,
    "max": lambda spec: spec["threshold"] - 1,
}
BAD = {
    "equals": lambda spec: "Broken",
    "min": lambda spec: spec["threshold"] - 1,
    "max": lambda spec: spec["threshold"] + 1,
}


def make_alert(rule, run_id, observed=None):
    alert = {
        "alert_id": f"demo-{rule}-{run_id}",
        "alert_rule": rule,
        "severity": "Sev2",
        "resource_id": f"/subscriptions/demo/resourceGroups/rg-lab/providers/demo/{rule}-{run_id}",
        "description": f"Simulated {rule}",
    }
    if observed is not None:
        spec = RULES[rule]["recovery"]
        alert["post_remediation_state"] = {spec["check"]: observed}
    return alert


def main():
    run_id = int(time.time())
    rows = []
    for rule, cfg in RULES.items():
        spec = cfg["recovery"]
        cases = [
            ("awaiting", None),
            ("recovered", GOOD[spec["mode"]](spec)),
            ("failed", BAD[spec["mode"]](spec)),
        ]
        for label, observed in cases:
            case_id = f"{run_id}-{label}"
            result = process_and_update_incident(make_alert(rule, case_id, observed))
            rows.append((rule, label, result["workflow_status"],
                         result["incident_number"], result["incident_state"]))

    print(f"{'Rule':<28}{'Case':<11}{'Workflow status':<34}{'Incident':<11}State")
    for r in rows:
        print(f"{r[0]:<28}{r[1]:<11}{r[2]:<34}{r[3]:<11}{r[4]}")

    expected = {"awaiting": "New", "recovered": "Resolved", "failed": "New"}
    bad = [r for r in rows if r[4] != expected[r[1]]]
    print(f"\n{len(rows)} cases, {len(bad)} unexpected")
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except requests.ConnectionError:
        print("Mock ServiceNow is not running. Start: python mock_servicenow.py")
        sys.exit(2)
