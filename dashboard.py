"""Light local dashboard for IYAV (POC).

Triggers simulated alerts through the same workflow + mock ServiceNow
used by the demo scripts. Needs the mock server on port 8090.
UI lives in dashboard_page.html.
Run: python dashboard.py  then open http://127.0.0.1:8080
"""
from pathlib import Path

import requests
from flask import Flask, jsonify, request

from rules import RULES
from workflow_service import SERVICENOW_URL, process_and_update_incident

app = Flask(__name__)

PAGE_FILE = Path(__file__).with_name("dashboard_page.html")

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


def build_alert(rule, instance, case):
    spec = RULES[rule]["recovery"]
    alert = {
        "alert_id": f"dash-{rule}-{instance}",
        "alert_rule": rule,
        "severity": "Sev2",
        "resource_id": f"/subscriptions/demo/resourceGroups/rg-lab/providers/demo/{rule}/{instance}",
        "description": f"Simulated {rule} on {instance}",
    }
    if case == "recovered":
        alert["post_remediation_state"] = {spec["check"]: GOOD[spec["mode"]](spec)}
    elif case == "failed":
        alert["post_remediation_state"] = {spec["check"]: BAD[spec["mode"]](spec)}
    return alert


@app.get("/api/scenarios")
def scenarios():
    return jsonify([
        {"rule": name, "action": cfg["action"], "check": cfg["recovery"]["check"]}
        for name, cfg in RULES.items()
    ])


@app.post("/api/trigger")
def trigger():
    data = request.get_json(silent=True) or {}
    rule = data.get("rule")
    case = data.get("case")
    instance = (data.get("instance") or "vm-demo").strip() or "vm-demo"
    if rule not in RULES or case not in ("awaiting", "recovered", "failed"):
        return jsonify({"error": "invalid rule or case"}), 400
    try:
        result = process_and_update_incident(build_alert(rule, instance, case))
    except requests.RequestException:
        return jsonify({"error": "Mock ServiceNow not reachable on port 8090"}), 503
    result["rule"] = rule
    result["case"] = case
    result["instance"] = instance
    return jsonify(result)


@app.get("/api/incidents")
def incidents():
    try:
        resp = requests.get(f"{SERVICENOW_URL}/api/incidents", timeout=5)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException:
        return jsonify({"error": "Mock ServiceNow not reachable on port 8090"}), 503


@app.get("/")
def index():
    return PAGE_FILE.read_text(encoding="utf-8-sig")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
