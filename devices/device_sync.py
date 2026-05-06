import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def device_sync():
    """
    Sends a sync request to a managed device via Microsoft Graph API.
    Forces the device to check in with Intune immediately.
    """
    print("\n=== Microsoft Graph: Sync Device ===")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices",
        headers=headers
    )
    if response.status_code != 200:
        print(f"❌ Failed to fetch devices (HTTP {response.status_code}):")
        print(response.text)
        return

    devices = response.json().get("value", [])
    if not devices:
        print("No managed devices found.")
        return

    print("\nEnrolled devices:")
    for i, d in enumerate(devices, start=1):
        print(f"  {i}. {d.get('deviceName','N/A')}  ({d.get('operatingSystem','N/A')})  [{d.get('complianceState','N/A')}]")

    choice = input("\nEnter device number to sync: ").strip()
    try:
        device = devices[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return

    confirm = input(f"\nSend sync to '{device.get('deviceName')}'? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    response = requests.post(
        f"https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/{device['id']}/syncDevice",
        headers=headers
    )

    if response.status_code == 204:
        print(f"\n✅ Sync request sent to '{device.get('deviceName')}'. Device will check in shortly.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        device_sync()
    except Exception as e:
        print(f"Critical error: {e}")
