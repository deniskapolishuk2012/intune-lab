import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

# All states that are NOT compliant
NON_COMPLIANT_STATES = {"noncompliant", "conflict", "error", "unknown", "inGracePeriod"}

def non_compliant_devices():
    """
    Reports all managed devices that are NOT compliant.
    Fetches all devices and filters client-side (OData filter for complianceState
    is unreliable in Graph API for managedDevices).
    """
    print("\n=== Report: Non-Compliant Devices ===")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    url = (
        "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices"
        "?$select=deviceName,userPrincipalName,operatingSystem,osVersion,"
        "complianceState,lastSyncDateTime,managementState,id"
    )

    all_devices = []
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed (HTTP {response.status_code}):")
            print(response.text)
            return
        data = response.json()
        all_devices.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    non_compliant = [
        d for d in all_devices
        if d.get("complianceState", "").lower() in NON_COMPLIANT_STATES
        or d.get("complianceState", "").lower() != "compliant"
    ]

    print(f"\nTotal managed devices: {len(all_devices)}")
    print(f"  ✅ Compliant:     {len(all_devices) - len(non_compliant)}")
    print(f"  ⚠️  Non-compliant: {len(non_compliant)}")

    if not non_compliant:
        print("\n✅ All managed devices are compliant.")
        return

    print(f"\nNon-compliant devices:\n")
    print(f"{'#':<4} {'Device Name':<25} {'Owner':<35} {'OS':<10} {'State':<20} {'Last Sync'}")
    print("-" * 115)

    for i, d in enumerate(non_compliant, start=1):
        print(
            f"{i:<4} {d.get('deviceName','N/A'):<25} "
            f"{d.get('userPrincipalName','N/A'):<35} "
            f"{d.get('operatingSystem','N/A'):<10} "
            f"{d.get('complianceState','N/A'):<20} "
            f"{d.get('lastSyncDateTime','N/A')}"
        )

    print(f"\nTip: Use device_sync.py to force a sync, then recheck compliance.")

if __name__ == "__main__":
    try:
        non_compliant_devices()
    except Exception as e:
        print(f"Critical error: {e}")
