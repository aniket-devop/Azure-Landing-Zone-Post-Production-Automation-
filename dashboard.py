"""Light local dashboard for IYAV (POC).

Triggers simulated alerts through the same workflow + mock ServiceNow
used by the demo scripts. Needs the mock server on port 8090.
Run: python dashboard.py  then open http://127.0.0.1:8080
"""
import requests
from flask import Flask, jsonify, request

from rules import RULES
from workflow_service import SERVICENOW_URL, process_and_update_incident

app = Flask(__name__)

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


PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>IYAV Dashboard</title>
<style>
body{font-family:Segoe UI,Arial,sans-serif;margin:24px;background:#f4f6f8;color:#1b1f23}
h1{margin:0 0 4px} .sub{color:#555;margin-bottom:16px}
.card{background:#fff;border-radius:8px;padding:16px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.12)}
select,input,button{padding:8px 10px;font-size:14px;margin-right:6px;border-radius:4px;border:1px solid #bbb}
button{cursor:pointer;color:#fff;border:0}
.b1{background:#0b6bcb}.b2{background:#1a7f37}.b3{background:#c62828}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #e3e6e9}
.New{color:#c62828;font-weight:600}.Resolved{color:#1a7f37;font-weight:600}
#err{color:#c62828;margin-top:8px}
.note{font-size:12px;color:#666;margin-top:8px}
</style></head><body>
<h1>IYAV Self-Healing Dashboard</h1>
<div class="sub">POC: remediation is dry-run, observations are simulated, local mock ServiceNow only.</div>

<div class="card">
<select id="rule"></select>
<input id="instance" value="vm-demo" size="14" title="resource instance name">
<button class="b1" onclick="fire('awaiting')">Alert aaya</button>
<button class="b2" onclick="fire('recovered')">Recovered</button>
<button class="b3" onclick="fire('failed')">Failed</button>
<div id="err"></div>
<div class="note">Same scenario + same instance twice = same incident reused (dedup). Recovered resolves it.</div>
</div>

<div class="card"><b>Workflow results (this session)</b>
<table><thead><tr><th>Time</th><th>Scenario</th><th>Instance</th><th>Case</th><th>Workflow status</th><th>Incident</th><th>State</th></tr></thead>
<tbody id="results"></tbody></table></div>

<div class="card"><b>Mock ServiceNow incidents (live, latest 15)</b>
<table><thead><tr><th>Number</th><th>State</th><th>Description</th></tr></thead>
<tbody id="incidents"></tbody></table></div>

<script>
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
function setErr(m){document.getElementById("err").textContent=m||"";}

async function loadScenarios(){
  var r=await fetch("/api/scenarios"); var list=await r.json();
  var sel=document.getElementById("rule");
  sel.innerHTML=list.map(function(s){return "<option value='"+esc(s.rule)+"'>"+esc(s.rule)+" ("+esc(s.check)+")</option>";}).join("");
}

async function fire(kind){
  setErr("");
  var body={rule:document.getElementById("rule").value,instance:document.getElementById("instance").value,case:kind};
  var r=await fetch("/api/trigger",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  var d=await r.json();
  if(!r.ok){setErr(d.error||"request failed");return;}
  var tr=document.createElement("tr");
  tr.innerHTML="<td>"+new Date().toLocaleTimeString()+"</td><td>"+esc(d.rule)+"</td><td>"+esc(d.instance)+"</td><td>"+esc(d.case)+"</td><td>"+esc(d.workflow_status)+"</td><td>"+esc(d.incident_number)+"</td><td class='"+esc(d.incident_state)+"'>"+esc(d.incident_state)+"</td>";
  var tb=document.getElementById("results"); tb.insertBefore(tr,tb.firstChild);
  loadIncidents();
}

async function loadIncidents(){
  try{
    var r=await fetch("/api/incidents"); var d=await r.json();
    if(!r.ok){setErr(d.error||"incidents unavailable");return;}
    var rows=d.slice(-15).reverse().map(function(i){
      return "<tr><td>"+esc(i.number)+"</td><td class='"+esc(i.state)+"'>"+esc(i.state)+"</td><td>"+esc(i.short_description)+"</td></tr>";
    }).join("");
    document.getElementById("incidents").innerHTML=rows;
  }catch(e){setErr("dashboard lost connection");}
}

loadScenarios(); loadIncidents(); setInterval(loadIncidents,2000);
</script></body></html>"""


@app.get("/")
def index():
    return PAGE


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
