import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def devices_without_bitlocker():
    """
    Reports Windows managed devices where BitLocker encryption is NOT enabled.
    Checks the 'isEncrypted' field returned by Graph API for each device.
    Only checks Windows devices — BitLocker is Windows-only.
    """
    print("\n=== Report: Windows Devices Without BitLocker ===")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    url = (
        "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices"
        "?$filter=operatingSystem eq 'Windows'"
        "&$select=deviceName,userPrincipalName,operatingSystem,osVersion,"
        "isEncrypted,complianceState,lastSyncDateTime,id"
    )

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed (HTTP {response.status_code}):")
        print(response.text)
        return

    devices     = response.json().get("value", [])
    unencrypted = [d for d in devices if not d.get("isEncrypted", False)]
    encrypted   = [d for d in devices if d.get("isEncrypted", False)]

    print(f"\nTotal Windows devices: {len(devices)}")
    print(f"  ✅ Encrypted (BitLocker ON):  {len(encrypted)}")
    print(f"  ⚠️  Not encrypted:            {len(unencrypted)}")

    if not unencrypted:
        print("\n✅ All Windows devices have BitLocker enabled.")
        return

    print(f"\nDevices WITHOUT BitLocker:\n")
    print(f"{'#':<4} {'Device Name':<25} {'Owner':<35} {'OS Version':<20} {'Compliance':<15} {'Last Sync'}")
    print("-" * 115)

    for i, d in enumerate(unencrypted, start=1):
        print(
            f"{i:<4} {d.get('deviceName','N/A'):<25} "
            f"{d.get('userPrincipalName','N/A'):<35} "
            f"{d.get('osVersion','N/A'):<20} "
            f"{d.get('complianceState','N/A'):<15} "
            f"{d.get('lastSyncDateTime','N/A')}"
        )

    print(f"\nTip: Assign the BitLocker configuration profile to these devices' groups.")

if __name__ == "__main__":
    try:
        devices_without_bitlocker()
    except Exception as e:
        print(f"Critical error: {e}")
