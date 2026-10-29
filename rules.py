"""Single source of truth for IYAV scenarios.

Adding a scenario = adding one entry here.
action   : approved remediation action (always simulated / dry-run)
recovery : how recovery is verified (mode: min | max | equals)
Observation field names below are simulated, not real Azure metric names.
"""
from typing import Any, Dict

RULES: Dict[str, Dict[str, Any]] = {
    "Disk-Space-Low": {
        "action": "clear_temp_files",
        "recovery": {"check": "disk_free_percent", "mode": "min", "threshold": 20},
    },
    "Application-Health-Failure": {
        "action": "restart_app",
        "recovery": {"check": "app_health_status", "mode": "equals", "expected": "Healthy"},
    },
    "Backup-Job-Failure": {
        "action": "retry_backup",
        "recovery": {"check": "last_backup_status", "mode": "equals", "expected": "Succeeded"},
    },
    "VM-Heartbeat-Lost": {
        "action": "restart_vm",
        "recovery": {"check": "heartbeat_status", "mode": "equals", "expected": "Healthy"},
    },
    "Policy-Tag-Noncompliant": {
        "action": "apply_required_tags",
        "recovery": {"check": "compliance_state", "mode": "equals", "expected": "Compliant"},
    },
    "Certificate-Expiring": {
        "action": "renew_certificate",
        "recovery": {"check": "cert_days_to_expiry", "mode": "min", "threshold": 30},
    },
    "Network-DNS-Failure": {
        "action": "flush_dns_and_retest",
        "recovery": {"check": "dns_resolution_status", "mode": "equals", "expected": "Resolved"},
    },
    "SLA-Breach-Risk": {
        "action": "escalate_to_resolver_group",
        "recovery": {"check": "sla_remaining_percent", "mode": "min", "threshold": 25},
    },
    "High-CPU-Utilization": {
        "action": "scale_up_vm",
        "recovery": {"check": "cpu_percent", "mode": "max", "threshold": 80},
    },
    "Service-Stopped": {
        "action": "restart_service",
        "recovery": {"check": "service_status", "mode": "equals", "expected": "Running"},
    },
}
