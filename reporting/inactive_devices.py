import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from datetime import datetime, timezone, timedelta
from core.auth import get_access_token

def inactive_devices():
    """
    Reports managed devices that have not synced within a specified number of days.
    Default threshold: 30 days. Useful for identifying stale/orphaned devices.
    """
    print("\n=== Report: Inactive Devices ===")

    days_input = input("Show devices inactive for more than how many days? [30]: ").strip()
    try:
        threshold_days = int(days_input) if days_input else 30
    except ValueError:
        threshold_days = 30

    cutoff = datetime.now(timezone.utc) - timedelta(days=threshold_days)
    print(f"\nLooking for devices with no sync since: {cutoff.strftime('%Y-%m-%d')} ({threshold_days} days ago)")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    url = (
        "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices"
        "?$select=deviceName,userPrincipalName,operatingSystem,lastSyncDateTime,"
        "complianceState,managementState,enrolledDateTime,id"
    )

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed (HTTP {response.status_code}):")
        print(response.text)
        return

    all_devices = response.json().get("value", [])
    inactive = []

    for d in all_devices:
        last_sync_str = d.get("lastSyncDateTime")
        if not last_sync_str:
            inactive.append(d)
            continue
        try:
            last_sync = datetime.fromisoformat(last_sync_str.replace("Z", "+00:00"))
            if last_sync < cutoff:
                inactive.append(d)
        except ValueError:
            inactive.append(d)

    if not inactive:
        print(f"\n✅ No devices inactive for more than {threshold_days} days.")
        return

    print(f"\n⚠️  Found {len(inactive)} inactive device(s):\n")
    print(f"{'#':<4} {'Device Name':<25} {'Owner':<35} {'OS':<10} {'Last Sync':<25} {'Compliance'}")
    print("-" * 115)

    for i, d in enumerate(inactive, start=1):
        print(
            f"{i:<4} {d.get('deviceName','N/A'):<25} "
            f"{d.get('userPrincipalName','N/A'):<35} "
            f"{d.get('operatingSystem','N/A'):<10} "
            f"{d.get('lastSyncDateTime','Never'):<25} "
            f"{d.get('complianceState','N/A')}"
        )

    print(f"\nTotal inactive: {len(inactive)}")
    print("Tip: Consider retiring stale devices using retire_device.py.")

if __name__ == "__main__":
    try:
        inactive_devices()
    except Exception as e:
        print(f"Critical error: {e}")
