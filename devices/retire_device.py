import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def retire_device():
    """
    Retires a managed device via Microsoft Graph API.
    Removes company data and unenrolls the device — personal data is NOT affected.
    """
    print("\n=== Microsoft Graph: Retire Device ===")
    print("ℹ️  Retire removes company data and unenrolls the device.")
    print("   Personal data is NOT affected.\n")

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

    choice = input("\nEnter device number to retire: ").strip()
    try:
        device = devices[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return

    confirm = input(f"\n⚠️  Retire '{device.get('deviceName')}'? This will unenroll it from Intune. [y/N]: ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    response = requests.post(
        f"https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/{device['id']}/retire",
        headers=headers
    )

    if response.status_code == 204:
        print(f"\n✅ Retire action sent to '{device.get('deviceName')}'.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        retire_device()
    except Exception as e:
        print(f"Critical error: {e}")
