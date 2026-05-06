import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def wipe_device():
    """
    Sends a full wipe command to a managed device via Microsoft Graph API.
    ⚠️  DESTRUCTIVE: Erases ALL data and resets device to factory defaults.
    Use retire_device.py for a safer option that preserves personal data.
    """
    print("\n=== Microsoft Graph: Wipe Device ===")
    print("⚠️  WARNING: Wipe will ERASE ALL DATA on the device (factory reset).")
    print("   For a safer option, use retire_device.py instead.\n")

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

    print("Enrolled devices:")
    for i, d in enumerate(devices, start=1):
        print(f"  {i}. {d.get('deviceName','N/A')}  ({d.get('operatingSystem','N/A')})  owner: {d.get('userPrincipalName','N/A')}")

    choice = input("\nEnter device number to wipe: ").strip()
    try:
        device = devices[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return

    confirm1 = input(f"\n⚠️  Are you sure you want to WIPE '{device.get('deviceName')}'? [y/N]: ").strip().lower()
    if confirm1 != "y":
        print("Cancelled.")
        return

    confirm2 = input(f"⚠️  FINAL WARNING: Type WIPE to confirm: ").strip()
    if confirm2 != "WIPE":
        print("Cancelled. (You must type WIPE in uppercase to confirm.)")
        return

    response = requests.post(
        f"https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/{device['id']}/wipe",
        json={"keepEnrollmentData": False, "keepUserData": False},
        headers={**headers, "Content-Type": "application/json"}
    )

    if response.status_code == 204:
        print(f"\n✅ Wipe action sent to '{device.get('deviceName')}'. Device will factory reset shortly.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        wipe_device()
    except Exception as e:
        print(f"Critical error: {e}")
