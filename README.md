# IYAV - Azure Landing Zone Self-Healing Automation (POC)

Pipeline: Monitor -> Detect -> Correlate -> Diagnose -> Remediate -> Verify -> ServiceNow Update

**This is a local proof of concept. Nothing here talks to real Azure or a real ServiceNow.**
Remediation is dry-run only (`resource_changed: false`). Recovery observations are simulated.

## What is verified (by automated tests and a live local demo)

- Alert processing, correlation id, diagnosis and dry-run remediation.
- Recovery verification before resolving, for 3 rules: Disk-Space-Low, Application-Health-Failure, Backup-Job-Failure.
- Recovery outcomes: verified (Resolved), failed (incident stays New), no observation (awaiting verification), manual override.
- Duplicate-ticket control: an open incident with the same correlation id is reused; a Resolved one is not.
- Mock ServiceNow refuses to Resolve an incident without verified recovery (HTTP 409).
- Azure Monitor Common Alert Schema parser, tested against sample payloads only (not live Azure).

Run tests: `python -m pytest -q`
Run demo: start `python mock_servicenow.py`, then `python demo_workflow.py`

## Use case status

| # | Use case | Status |
|---|----------|--------|
| 1 | VM Health | Planned |
| 2 | Disk & Capacity | Simulated (recovery check + dry-run remediation) |
| 3 | Policy Compliance | Planned |
| 4 | Application Health | Simulated (recovery check) |
| 5 | Certificate Expiry | Planned |
| 6 | Backup Monitoring | Simulated (recovery check) |
| 7 | Network Issues | Planned |
| 8 | SLA Management | Planned |

## Not implemented

- Real Azure: Monitor, Log Analytics, Resource Graph, Policy, Logic Apps, Functions deployment.
- Real ServiceNow integration (a local Flask mock is used).
- Real remediation (everything is dry-run).
- Work notes and In-Progress state on failed recovery.
- Generic rule table, dashboard.

## Security

No credentials or subscription IDs are stored in code. Real integrations would use environment variables or managed identity.
