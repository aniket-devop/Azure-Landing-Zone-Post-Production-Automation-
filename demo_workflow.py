import json

from workflow_service import process_and_update_incident


alert = {
    "alert_id": "IYAV-DEMO-DISK-001",
    "alert_rule": "Disk-Space-Low",
    "severity": "Sev2",
    "resource_id": "/subscriptions/demo/resourceGroups/rg-lab/providers/Microsoft.Compute/virtualMachines/vm-demo",
    "description": "Disk capacity warning detected",
}

print("=== RUN 1: Alert detected; recovery not verified ===")
first = process_and_update_incident(alert)
print(json.dumps(first, indent=2))

print("\n=== RUN 2: Recovery verification supplied ===")
second = process_and_update_incident(
    alert,
    recovery_verified=True,
)
print(json.dumps(second, indent=2))
