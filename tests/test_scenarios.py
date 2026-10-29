import pytest

from rules import RULES
from self_healing_workflow import run_workflow

RESOURCE = (
    "/subscriptions/demo/resourceGroups/rg-lab/providers/"
    "Microsoft.Compute/virtualMachines/vm-demo"
)

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


def _alert(rule, observed=None):
    alert = {
        "alert_id": f"test-{rule}",
        "alert_rule": rule,
        "severity": "Sev2",
        "resource_id": RESOURCE,
        "description": "simulated scenario test",
    }
    if observed is not None:
        spec = RULES[rule]["recovery"]
        alert["post_remediation_state"] = {spec["check"]: observed}
    return alert


def test_ten_scenarios_configured():
    assert len(RULES) == 10


@pytest.mark.parametrize("rule", list(RULES))
def test_scenario_recovers(rule):
    spec = RULES[rule]["recovery"]
    result = run_workflow(_alert(rule, GOOD[spec["mode"]](spec)))
    assert result["workflow_status"] == "recovery_verified"
    assert result["incident_state"] == "Resolved"
    assert result["remediation"]["resource_changed"] is False


@pytest.mark.parametrize("rule", list(RULES))
def test_scenario_recovery_fails(rule):
    spec = RULES[rule]["recovery"]
    result = run_workflow(_alert(rule, BAD[spec["mode"]](spec)))
    assert result["workflow_status"] == "recovery_failed"
    assert result["incident_state"] == "New"


@pytest.mark.parametrize("rule", list(RULES))
def test_scenario_awaits_without_observation(rule):
    result = run_workflow(_alert(rule))
    assert result["workflow_status"] == "awaiting_recovery_verification"
    assert result["incident_state"] == "New"
