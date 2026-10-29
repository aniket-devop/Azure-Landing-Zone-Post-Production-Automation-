import pytest

import recovery_verifier
from remediation_engine import APPROVED_ACTIONS, diagnose_alert
from recovery_verifier import RECOVERY_CHECKS, verify_recovery
from rules import RULES


@pytest.mark.parametrize("rule", list(RULES))
def test_every_rule_is_wired_everywhere(rule):
    assert RULES[rule]["action"] in APPROVED_ACTIONS
    assert rule in RECOVERY_CHECKS
    assert diagnose_alert({"alert_rule": rule})["action"] == RULES[rule]["action"]


def test_unknown_rule_needs_manual_investigation():
    result = diagnose_alert({"alert_rule": "Not-A-Rule"})
    assert result["action"] == "none"


def test_max_mode_recovered(monkeypatch):
    monkeypatch.setitem(
        recovery_verifier.RECOVERY_CHECKS,
        "X-Max",
        {"check": "cpu_percent", "mode": "max", "threshold": 80},
    )
    alert = {"alert_rule": "X-Max", "post_remediation_state": {"cpu_percent": 40}}
    assert verify_recovery(alert)["recovered"] is True


def test_max_mode_not_recovered(monkeypatch):
    monkeypatch.setitem(
        recovery_verifier.RECOVERY_CHECKS,
        "X-Max",
        {"check": "cpu_percent", "mode": "max", "threshold": 80},
    )
    alert = {"alert_rule": "X-Max", "post_remediation_state": {"cpu_percent": 95}}
    assert verify_recovery(alert)["recovered"] is False
