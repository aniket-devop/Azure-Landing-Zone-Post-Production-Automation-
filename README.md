# IYAV - Azure Landing Zone Self-Healing Automation (POC)

Pipeline: Monitor -> Detect -> Correlate -> Diagnose -> Remediate -> Verify -> ServiceNow Update

**This is a local proof of concept. Nothing here talks to real Azure or a real ServiceNow.**
Remediation is dry-run only (`resource_changed: false`). Recovery observations are simulated.

## What is verified (automated tests + live local demo)

- Alert validation, correlation id (hash of resource + rule), diagnosis, dry-run remediation.
- Recovery verification before resolving: verified (Resolved), failed (incident stays New), no observation (awaiting verification), manual override.
- Duplicate-ticket control: an open incident with the same correlation id is reused; a Resolved one is not (tests + live demo).
- Mock ServiceNow refuses to Resolve without verified recovery (HTTP 409).
- Azure Monitor Common Alert Schema parser, tested against sample payloads only, not live Azure.
- Generic rule table (`rules.py`): adding a scenario = adding one entry. Remediation, approved actions and recovery checks are all derived from it.

Tests: `python -m pytest -q` (92 passed at last run). Tests do not need the mock server.
Demo: start `python mock_servicenow.py`, then `python demo_workflow.py`.

## Scenarios (10, all simulated)

| # | Scenario | Rule | Check | Status |
|---|----------|------|-------|--------|
| 1 | Disk & Capacity | Disk-Space-Low | disk_free_percent >= 20 | Simulated, in live demo |
| 2 | Application Health | Application-Health-Failure | app_health_status == Healthy | Simulated |
| 3 | Backup Monitoring | Backup-Job-Failure | last_backup_status == Succeeded | Simulated |
| 4 | VM Health | VM-Heartbeat-Lost | heartbeat_status == Healthy | Simulated, workflow tests only |
| 5 | Policy Compliance | Policy-Tag-Noncompliant | compliance_state == Compliant | Simulated, workflow tests only |
| 6 | Certificate Expiry | Certificate-Expiring | cert_days_to_expiry >= 30 | Simulated, workflow tests only |
| 7 | Network Issues | Network-DNS-Failure | dns_resolution_status == Resolved | Simulated, workflow tests only |
| 8 | SLA Management | SLA-Breach-Risk | sla_remaining_percent >= 25 | Simulated, workflow tests only |
| 9 | High CPU | High-CPU-Utilization | cpu_percent <= 80 | Simulated, workflow tests only |
| 10 | Service Stopped | Service-Stopped | service_status == Running | Simulated, workflow tests only |

"Simulated" means: observation fields are invented for this POC (not real Azure metric names),
and observations are supplied in the alert payload. No real resource is checked or changed.

## Not implemented

- Real Azure: Monitor, Log Analytics, Resource Graph, Policy, Logic Apps, Functions deployment.
- Real ServiceNow (a local Flask mock is used).
- Real remediation and real recovery observations (provider hook exists, only the simulated one is implemented).
- Work notes and In-Progress state on failed recovery.
- SLA timers and real escalation; the SLA scenario only checks a simulated percentage.
- Dashboard.

## Security

No credentials or subscription IDs are stored in code. Real integrations would use environment variables or managed identity.

## Live end-to-end demo (10 scenarios x 3 cases)

Start `python mock_servicenow.py`, then `python demo_all_scenarios.py`.
Each scenario runs through workflow + mock ServiceNow in three cases (awaiting, recovered, failed).
Last run: 30 cases, 0 unexpected. Observations are simulated; remediation is dry-run.
