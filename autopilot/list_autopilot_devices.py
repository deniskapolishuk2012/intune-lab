import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def list_autopilot_devices():
    """
    Lists all devices registered in Windows Autopilot via Microsoft Graph API.
    Uses beta endpoint — required for Autopilot device identities.
    """
    print("\n=== Microsoft Graph: List Autopilot Devices ===")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsAutopilotDeviceIdentities"

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

    if not all_devices:
        print("\nNo Autopilot devices found in your tenant.")
        print("Use upload_autopilot_device.py to register a device.")
        return

    print(f"\nFound {len(all_devices)} Autopilot device(s):\n")
    print(f"{'#':<4} {'Serial Number':<45} {'Manufacturer':<15} {'Model':<20} {'Profile Status':<25} {'Group Tag'}")
    print("-" * 125)

    for i, d in enumerate(all_devices, start=1):
        print(
            f"{i:<4} {d.get('serialNumber','N/A'):<45} "
            f"{d.get('manufacturer','N/A'):<15} "
            f"{d.get('model','N/A'):<20} "
            f"{d.get('deploymentProfileAssignmentStatus','N/A'):<25} "
            f"{d.get('groupTag','')}"
        )

if __name__ == "__main__":
    try:
        list_autopilot_devices()
    except Exception as e:
        print(f"Critical error: {e}")
