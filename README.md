<div align="center">

# IYAV: Self-Healing Automation for Azure Landing Zones

**Post-production incident automation proof of concept**

Monitor → Detect → Correlate → Diagnose → Remediate → Verify → ServiceNow Update

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-mock%20ServiceNow-000000?logo=flask&logoColor=white)
![pytest](https://img.shields.io/badge/tests-92%20passed%20(author--reported)-0A9EDC?logo=pytest&logoColor=white)
![Remediation](https://img.shields.io/badge/remediation-dry--run%20only-orange)
![Status](https://img.shields.io/badge/status-local%20POC-blueviolet)
![License](https://img.shields.io/badge/license-MIT-green)

[![Watch the demo video](docs/demo/video-thumbnail.png)](https://github.com/aniket-devop/Azure-Landing-Zone-Post-Production-Automation-/raw/refs/heads/main/docs/demo/azure_landing_zone_demo.mp4)

</div>

> [!IMPORTANT]
> **This is a local proof of concept (POC).** Nothing in this repository connects to a real Azure subscription or a real ServiceNow instance.
> - Remediation is **dry-run only** (`resource_changed: false`).
> - Recovery observations are **simulated** and are supplied in the alert payload.
> - ServiceNow is replaced by a **local Flask mock**.
>
> There is no Terraform, Bicep, or CI/CD workflow in this repository.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Problem Statement and Objectives](#2-problem-statement-and-objectives)
3. [Architecture and Workflow](#3-architecture-and-workflow)
4. [Technologies Used](#4-technologies-used)
5. [Repository Structure](#5-repository-structure)
6. [Prerequisites](#6-prerequisites)
7. [Installation](#7-installation)
8. [How to Run](#8-how-to-run)
9. [Supported Scenarios](#9-supported-scenarios)
10. [Configuration](#10-configuration)
11. [Demo](#11-demo)
12. [Validation Evidence](#12-validation-evidence)
13. [Security Considerations](#13-security-considerations)
14. [Troubleshooting](#14-troubleshooting)
15. [Current Limitations](#15-current-limitations)
16. [Future Improvements](#16-future-improvements)
17. [Author and Acknowledgements](#17-author-and-acknowledgements)

---

## 1. Overview

IYAV simulates how a post-production operations process for an Azure Landing Zone can handle common incidents automatically. An alert is validated, grouped under a correlation ID, diagnosed, remediated (dry-run), checked for recovery, and only then resolved in a ServiceNow-style ticketing system.

The central design rule is that **an incident is never resolved on faith**. A ticket moves to `Resolved` only after recovery has been verified or manually overridden. The mock ServiceNow API enforces this by returning HTTP `409` when a resolve is attempted without verified recovery.

| Capability | Description |
|---|---|
| Recovery gate | Resolve is blocked until recovery is verified. |
| Correlation | A hash of resource and rule produces a stable correlation ID. |
| Deduplication | An open incident with the same correlation ID is reused. |
| Rule-driven | Scenarios, actions, and recovery checks live in one table (`rules.py`). |
| Observability | Live dashboard showing pipeline stages and incident state. |
| Safe by default | Dry-run remediation only; no real resource is modified. |

## 2. Problem Statement and Objectives

**Problem.** In post-production cloud operations, the same alert can fire repeatedly, tickets get duplicated, and tickets are sometimes closed before the underlying issue is fixed.

**Objectives of this POC**

- Validate incoming alerts and derive a stable correlation ID (hash of resource and rule).
- Diagnose alerts and select an approved remediation action from a single rule table.
- Verify recovery before resolving a ticket.
- Avoid duplicate tickets by reusing an open incident with the same correlation ID.
- Make adding a new scenario a one-entry change in `rules.py`.
- Demonstrate the full flow locally with automated tests and a live dashboard.

## 3. Architecture and Workflow

All components run locally. The workflow core is `self_healing_workflow.py`, which chains the alert engine, remediation engine, and recovery verifier. `workflow_service.py` then calls the mock ServiceNow over HTTP.

```mermaid
flowchart TD
    A["Alert payload (simulated)"] --> B["alert_engine.process_alert<br/>validate and build correlation_id"]
    B --> C["remediation_engine.diagnose_alert<br/>diagnosis and action from rules"]
    C -->|"action = none"| M["workflow_status:<br/>manual_investigation_required"]
    C -->|"action found"| D["execute_remediation<br/>dry_run = True"]
    D --> E{"recovery_verified<br/>override passed?"}
    E -->|"yes"| OK["recovery source: manual<br/>incident_state: Resolved"]
    E -->|"no"| F["recovery_verifier.verify_recovery<br/>check observation"]
    F -->|"no observation"| W["awaiting_recovery_verification<br/>incident stays New"]
    F -->|"issue still present"| X["recovery_failed<br/>incident stays open"]
    F -->|"issue gone"| OK2["recovery_verified<br/>incident_state: Resolved"]
    OK --> S["workflow_service<br/>POST /api/incidents"]
    OK2 --> S
    W --> S
    X --> S
    S --> N["Mock ServiceNow (Flask, port 8090)<br/>reuse open incident with same correlation_id"]
    OK --> P["PATCH /api/incidents/:number<br/>state: Resolved"]
    OK2 --> P
    P --> N
```

### Pipeline stages

| Stage | What happens | Implemented in |
|---|---|---|
| Monitor / Detect | An alert payload is received and validated. | `alert_engine.py` (`process_alert`) |
| Correlate | A correlation ID is derived from a hash of the resource and the alert rule. Alerts for the same resource and rule share one ID. | `alert_engine.py` |
| Diagnose | The alert rule is looked up in the rule table to produce a diagnosis and a remediation action. If no action applies, the workflow stops with `manual_investigation_required`. | `remediation_engine.py` (`diagnose_alert`), `rules.py` |
| Remediate | The approved action is executed in dry-run mode only. No real resource is changed. | `remediation_engine.py` (`execute_remediation`) |
| Verify | Recovery is decided in this order: (1) manual override `recovery_verified=True`; (2) otherwise the verifier compares a simulated post-remediation observation with the rule's check. | `recovery_verifier.py`, `self_healing_workflow.py` |
| ServiceNow update | An incident is created, or the existing open one with the same correlation ID is reused. If recovery is verified, the incident is patched to `Resolved`. | `workflow_service.py`, `mock_servicenow.py` |

### Workflow outcomes

| `workflow_status` | Meaning | Incident state |
|---|---|---|
| `manual_investigation_required` | Diagnosis produced no automated action. | `New` |
| `awaiting_recovery_verification` | No observation available yet. | `New` |
| `recovery_failed` | Observation shows the issue is still present. | Stays open (`New`) |
| `recovery_verified` | Manual override or verified observation. | `Resolved` |

### Supporting components

- **Azure Monitor alert parser.** `azure_alert_parser.py` parses the Azure Monitor Common Alert Schema. It has been tested against sample payloads only, not against live Azure.
- **Azure Function stub.** `function_app.py` defines an Azure Functions app with a single anonymous `GET /health` route that returns `{"project": "IYAV", "status": "healthy", "mode": "foundation"}`. It is a foundation stub and is not yet connected to the workflow.

## 4. Technologies Used

| Technology | Usage in this repository |
|---|---|
| Python | Workflow, rules, engines, demos, dashboard (type hints such as `dict[str, Any]` imply Python 3.9+) |
| Flask | Mock ServiceNow API and dashboard server |
| requests | HTTP client used by `workflow_service.py` to call the mock ServiceNow |
| pytest | Automated test suite in `tests/` |
| azure-functions | Azure Functions Python library used by the `function_app.py` health stub |
| HTML | Dashboard UI (`dashboard_page.html`) |

Dependencies in `requirements.txt`: `azure-functions`, `pytest`, `Flask`, `requests`.

## 5. Repository Structure

```text
.
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── host.json                    # Azure Functions host configuration
├── function_app.py              # Azure Functions app: GET /health stub
│
├── rules.py                     # Rule table: one entry per scenario
├── alert_engine.py              # Alert validation, correlation id
├── azure_alert_parser.py        # Azure Monitor Common Alert Schema parser
├── alert_processor.py           <!-- TODO: confirm purpose and update this comment -->
├── remediation_engine.py        # Diagnosis and dry-run remediation
├── recovery_verifier.py         # Post-remediation recovery check
├── self_healing_workflow.py     # Orchestrates the workflow
├── workflow_service.py          # Calls mock ServiceNow (create / resolve incident)
├── mock_servicenow.py           # Local Flask mock of ServiceNow
│
├── demo_workflow.py             # Demo against the mock server
├── demo_all_scenarios.py        # 10 scenarios x 3 cases end-to-end demo
├── dashboard.py                 # Live dashboard server (port 8080)
├── dashboard_page.html          # Dashboard UI
│
├── tests/                       # pytest suite
└── docs/
    ├── demo/                    # Demo video and thumbnail
    └── screenshots/             # Dashboard screenshots
```

## 6. Prerequisites

- Python 3.9 or newer (the version is not pinned in the repository)
- pip
- Git
- A modern web browser for the dashboard

**Azure setup:** none required. This POC does not call Azure, so no subscription, Azure CLI, or credentials are needed.

**Optional:** [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local) to run the `/health` stub locally with `func start`.

## 7. Installation

```bash
# 1. Clone the repository
git clone https://github.com/aniket-devop/Azure-Landing-Zone-Post-Production-Automation-.git
cd Azure-Landing-Zone-Post-Production-Automation-

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

No secrets or `.env` file are needed. See [Configuration](#10-configuration).

## 8. How to Run

### 8.1 Automated tests

The tests do not need the mock server.

```bash
python -m pytest -q
```

### 8.2 Command-line demos

Each demo needs the mock ServiceNow running, so use two terminals.

**Terminal 1:** start mock ServiceNow (port 8090)

```bash
python mock_servicenow.py
```

**Terminal 2:** run a demo

```bash
# Single-workflow demo
python demo_workflow.py

# All 10 scenarios x 3 cases (awaiting, recovered, failed)
python demo_all_scenarios.py
```

### 8.3 Live dashboard

**Terminal 1:** `python mock_servicenow.py`
**Terminal 2:** `python dashboard.py`

Then open <http://127.0.0.1:8080>.

In the dashboard you can:

1. Pick a scenario and enter an instance name.
2. Trigger **Alert**, **Recovered**, or **Failed**.
3. Optionally click **Run auto demo** to run through all scenarios.
4. Watch the pipeline stages, the workflow results table, and the live mock ServiceNow incidents.

Expected behavior: triggering the same scenario and instance twice reuses the open incident (deduplication); **Recovered** resolves it; **Failed** leaves it open.

### 8.4 Azure Function health stub (optional)

```bash
func start
# the default route prefix is /api
# curl http://localhost:7071/api/health   <!-- TODO: confirm against host.json -->
```

## 9. Supported Scenarios

There are 10 scenarios, all simulated. The observation fields are invented for this POC (they are not real Azure metric names) and are supplied in the alert payload. No real resource is checked or changed.

| # | Scenario | Rule | Recovery check | Status |
|---|---|---|---|---|
| 1 | Disk & Capacity | `Disk-Space-Low` | `disk_free_percent >= 20` | Simulated, in live demo |
| 2 | Application Health | `Application-Health-Failure` | `app_health_status == Healthy` | Simulated |
| 3 | Backup Monitoring | `Backup-Job-Failure` | `last_backup_status == Succeeded` | Simulated |
| 4 | VM Health | `VM-Heartbeat-Lost` | `heartbeat_status == Healthy` | Simulated, workflow tests only |
| 5 | Policy Compliance | `Policy-Tag-Noncompliant` | `compliance_state == Compliant` | Simulated, workflow tests only |
| 6 | Certificate Expiry | `Certificate-Expiring` | `cert_days_to_expiry >= 30` | Simulated, workflow tests only |
| 7 | Network Issues | `Network-DNS-Failure` | `dns_resolution_status == Resolved` | Simulated, workflow tests only |
| 8 | SLA Management | `SLA-Breach-Risk` | `sla_remaining_percent >= 25` | Simulated, workflow tests only |
| 9 | High CPU | `High-CPU-Utilization` | `cpu_percent <= 80` | Simulated, workflow tests only |
| 10 | Service Stopped | `Service-Stopped` | `service_status == Running` | Simulated, workflow tests only |

**Adding a scenario:** remediation, approved actions, and recovery checks are all derived from the generic rule table in `rules.py`, so a new scenario is a single new entry there.

## 10. Configuration

The current code does not read any environment variables. Settings are constants or defaults:

| Setting | Value | Where |
|---|---|---|
| Mock ServiceNow base URL | `http://127.0.0.1:8090` | `SERVICENOW_URL` constant in `workflow_service.py` |
| Dashboard address | `http://127.0.0.1:8080` | `dashboard.py` |
| HTTP timeout to mock ServiceNow | 5 seconds | `workflow_service.py` |

To point the workflow at a different mock server, edit `SERVICENOW_URL` in `workflow_service.py`.

Real integrations (Azure, ServiceNow) are not implemented. If you add them later, read credentials from environment variables or use managed identity, and never commit them. See [Security Considerations](#13-security-considerations).

## 11. Demo

### Video

A screen recording of the live dashboard is included in this repository.

- In-repo video: [`docs/demo/azure_landing_zone_demo.mp4`](https://github.com/aniket-devop/Azure-Landing-Zone-Post-Production-Automation-/raw/refs/heads/main/docs/demo/azure_landing_zone_demo.mp4)
- Hosted version (optional): `<ADD YOUTUBE / DRIVE / RELEASE URL HERE>`

### Screenshots

Both screenshots are taken from the demo recording and show the dashboard at `http://127.0.0.1:8080`.

**Completed pipeline (`Service-Stopped`)**

![Dashboard with completed pipeline](docs/screenshots/01-dashboard-pipeline-resolved.png)

A simulated `Service-Stopped` run: all seven pipeline stages complete, the remediation is shown as `restart_service (dry-run)`, and the incident ends as **Resolved** with `recovery_verified`.

**Awaiting verification (`Disk-Space-Low`)**

![Dashboard awaiting verification](docs/screenshots/02-dashboard-awaiting-verification.png)

A simulated `Disk-Space-Low` alert for which recovery has not yet been reported: status `awaiting_recovery_verification`, incident state **New**.

## 12. Validation Evidence

### Behavior covered

- Alert validation, correlation ID generation, diagnosis, and dry-run remediation.
- Recovery verification before resolve, across four paths: verified (Resolved), failed (incident stays New), no observation (awaiting verification), and manual override.
- Duplicate-ticket control: an open incident with the same correlation ID is reused; a Resolved one is not.
- The mock ServiceNow refuses to resolve without verified recovery (HTTP `409`).
- Azure Monitor Common Alert Schema parsing, against sample payloads only.

### Author-reported results

| Check | Reported result |
|---|---|
| `python -m pytest -q` | 92 passed at last run |
| `python demo_all_scenarios.py` | 30 cases (10 scenarios × 3 cases), 0 unexpected |

> [!NOTE]
> These figures were reported by the author and were not re-executed while preparing this README.

### Not covered by automated tests

- The dashboard has no automated test yet; it is demonstrated through the video and screenshots above.

## 13. Security Considerations

- No credentials or subscription IDs are stored in the code.
- Remediation is dry-run only, so no real resource can be modified by this POC.
- Recovery cannot be marked verified without either an observation or an explicit manual override, and the mock ServiceNow rejects resolving without verified recovery.
- The Azure Function stub uses `AuthLevel.ANONYMOUS`. This is acceptable for a local health stub only. Do not deploy it publicly without reviewing the auth level.
- The mock ServiceNow and dashboard are intended for local use (`127.0.0.1`) and have no authentication.
- Before any real integration: use environment variables or managed identity, keep secrets out of Git, and apply least-privilege roles to any remediation identity.

## 14. Troubleshooting

| Symptom | Likely cause | Resolution |
|---|---|---|
| `ConnectionError` / connection refused on `127.0.0.1:8090` | Mock ServiceNow is not running | Start `python mock_servicenow.py` first, in its own terminal. |
| Dashboard does not show "Mock ServiceNow connected" | Same as above | Start the mock server, then refresh `http://127.0.0.1:8080`. |
| `Address already in use` | Port 8080 or 8090 is taken | Stop the other process, or change the port in the relevant script. |
| `ModuleNotFoundError` | Dependencies not installed or venv not active | Activate the venv and run `pip install -r requirements.txt`. |
| PowerShell blocks `Activate.ps1` | Execution policy | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`, then activate again. |
| HTTP `409` when resolving an incident | Recovery was not verified | Expected behavior. Send a recovered observation, or use the manual override. |
| A second alert does not create a new ticket | Deduplication | Expected. An open incident with the same correlation ID is reused. |
| Incident stays `New` after a "Failed" run | Recovery check failed | Expected. Failed recovery leaves the incident open. |
| Tests fail unexpectedly | Environment mismatch | Confirm Python 3.9+ and a fresh `pip install -r requirements.txt`. The tests do not need the mock server. |

## 15. Current Limitations

Not implemented:

- Real Azure: Monitor, Log Analytics, Resource Graph, Policy, Logic Apps, and Functions deployment.
- Real ServiceNow (a local Flask mock is used instead).
- Real remediation and real recovery observations. A provider hook exists, but only the simulated provider is implemented.
- Work notes and an In-Progress state on failed recovery.
- SLA timers and real escalation. The SLA scenario only checks a simulated percentage.
- Terraform / Bicep infrastructure code and CI/CD workflows.
- An automated test for the dashboard.

## 16. Future Improvements

Ideas that follow from the current design (none are implemented):

- Replace the simulated observation provider with real Azure Monitor / Log Analytics queries through the existing provider hook.
- Feed live Azure Monitor Common Alert Schema payloads into the workflow via the Azure Function.
- Integrate with a real ServiceNow instance, including work notes and an In-Progress state on failed recovery.
- Add real remediation actions behind an approval gate, authenticated with managed identity.
- Move hardcoded settings (such as `SERVICENOW_URL`) into environment variables.
- Add tests for the dashboard and a GitHub Actions workflow that runs `pytest` on every push.
- Add Infrastructure as Code (Bicep or Terraform) for deploying the Function and supporting resources.

## 17. Author and Acknowledgements

👤 **Author**
**Aniket Kumar** · DevSecOps Engineer

[![GitHub](https://img.shields.io/badge/GitHub-aniket--devop-181717?logo=github)](https://github.com/aniket-devop)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-aniket484-0A66C2?logo=linkedin&logoColor=white)](https://linkedin.com/in/aniket484)
[![Email](https://img.shields.io/badge/Email-aniketkmr484%40gmail.com-D14836?logo=gmail&logoColor=white)](mailto:aniketkmr484@gmail.com)

🙏 Thanks to the mentors, learning resources, and open-source tools that supported this project.

📄 Licensed under the [MIT License](https://github.com/aniket-devop/Azure-Landing-Zone-Post-Production-Automation-/blob/main/LICENSE).

---

<div align="center">

*This README describes a local proof of concept. All observations are simulated, and no real Azure or ServiceNow resources are accessed or modified.*

⭐ If you found this useful, consider starring the repo!

</div>
