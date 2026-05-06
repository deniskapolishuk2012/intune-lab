import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def pick_device(token: str) -> dict | None:
    """Fetches device list and lets user pick one interactively."""
    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices",
        headers=headers
    )
    if response.status_code != 200:
        print(f"❌ Failed to fetch devices (HTTP {response.status_code}):")
        print(response.text)
        return None
    devices = response.json().get("value", [])
    if not devices:
        print("No managed devices found.")
        return None
    print("\nEnrolled devices:")
    for i, d in enumerate(devices, start=1):
        print(f"  {i}. {d.get('deviceName','N/A')}  ({d.get('operatingSystem','N/A')})")
    choice = input("\nEnter device number: ").strip()
    try:
        return devices[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return None

def device_details():
    """
    Shows detailed info for a specific managed device:
    owner, compliance state, OS version, last sync, enrollment date.
    """
    print("\n=== Microsoft Graph: Device Details ===")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    device = pick_device(token)
    if not device:
        return

    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/{device['id']}",
        headers=headers
    )
    if response.status_code != 200:
        print(f"❌ Failed (HTTP {response.status_code}):")
        print(response.text)
        return

    d = response.json()
    print(f"\n{'='*50}")
    print(f"  Device Name      : {d.get('deviceName', 'N/A')}")
    print(f"  Device ID        : {d.get('id', 'N/A')}")
    print(f"  Owner UPN        : {d.get('userPrincipalName', 'N/A')}")
    print(f"  Owner Display    : {d.get('userDisplayName', 'N/A')}")
    print(f"  OS               : {d.get('operatingSystem', 'N/A')} {d.get('osVersion', '')}")
    print(f"  Compliance State : {d.get('complianceState', 'N/A')}")
    print(f"  Management State : {d.get('managementState', 'N/A')}")
    print(f"  Enrollment Type  : {d.get('deviceEnrollmentType', 'N/A')}")
    print(f"  Last Sync        : {d.get('lastSyncDateTime', 'N/A')}")
    print(f"  Enrolled Date    : {d.get('enrolledDateTime', 'N/A')}")
    print(f"  Serial Number    : {d.get('serialNumber', 'N/A')}")
    print(f"  Manufacturer     : {d.get('manufacturer', 'N/A')}")
    print(f"  Model            : {d.get('model', 'N/A')}")
    print(f"  Azure AD Join    : {d.get('joinType', 'N/A')}")
    print(f"{'='*50}")

if __name__ == "__main__":
    try:
        device_details()
    except Exception as e:
        print(f"Critical error: {e}")
