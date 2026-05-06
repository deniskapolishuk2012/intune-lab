import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def list_devices():
    """
    Lists all managed devices enrolled in Intune via Microsoft Graph API.
    Displays device name, OS, compliance state, and last sync time.
    """
    print("\n=== Microsoft Graph: List Managed Devices ===")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    url      = "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices"
    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed (HTTP {response.status_code}):")
        print(response.text)
        return

    devices = response.json().get("value", [])
    if not devices:
        print("No managed devices found in your tenant.")
        return

    print(f"\nFound {len(devices)} device(s):\n")
    print(f"{'#':<4} {'Device Name':<30} {'OS':<10} {'Compliance':<15} {'Last Sync':<25} {'ID'}")
    print("-" * 110)
    for i, d in enumerate(devices, start=1):
        print(f"{i:<4} {d.get('deviceName','N/A'):<30} {d.get('operatingSystem','N/A'):<10} "
              f"{d.get('complianceState','N/A'):<15} {d.get('lastSyncDateTime','N/A'):<25} {d.get('id','N/A')}")

if __name__ == "__main__":
    try:
        list_devices()
    except Exception as e:
        print(f"Critical error: {e}")
