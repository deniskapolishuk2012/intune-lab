import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import re
import requests
from core.auth import get_access_token

def generate_nickname(name: str) -> str:
    nickname = name.lower()
    nickname = re.sub(r'[^a-z0-9_]', '_', nickname)
    nickname = re.sub(r'_+', '_', nickname)
    return nickname.strip('_')[:64] or "group"

def get_device_id(token: str, device_name: str) -> str | None:
    """
    Resolves a device name to its Azure AD object ID.
    Searches by displayName in Azure AD registered devices.
    """
    url     = f"https://graph.microsoft.com/v1.0/devices?$filter=displayName eq '{device_name}'"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        devices = response.json().get("value", [])
        if devices:
            return devices[0].get("id")
        print(f"  ⚠️  Device '{device_name}' not found in Azure AD.")
        return None
    print(f"  ⚠️  Failed to search for '{device_name}' (HTTP {response.status_code}).")
    return None

def create_device_group():
    """
    Creates an Azure AD security group for devices (computers).
    Members are resolved by device display name (computer name).

    Note: devices must be Azure AD joined or registered to appear here.
    """
    print("\n=== Microsoft Graph: Create Device Security Group ===")
    print("ℹ️  Add computers by their device name (e.g. DESKTOP-LAB01)\n")

    display_name  = input("Group name: ").strip()
    auto_nickname = generate_nickname(display_name)
    mail_nickname = input(f"Mail nickname [{auto_nickname}]: ").strip().replace(" ", "_") or auto_nickname
    description   = input("Description (optional): ").strip()

    print("\nAdd devices now? Enter device names one by one, empty line to finish.")
    device_names = []
    while True:
        name = input(f"  Device #{len(device_names)+1} (or Enter to finish): ").strip()
        if not name:
            break
        device_names.append(name)

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    device_ids = []
    if device_names:
        print("\nResolving devices...")
        for name in device_names:
            did = get_device_id(token, name)
            if did:
                device_ids.append(did)
                print(f"  ✅ Found: {name}")

    url     = "https://graph.microsoft.com/v1.0/groups"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    payload = {
        "displayName":     display_name,
        "mailNickname":    mail_nickname,
        "groupTypes":      [],
        "mailEnabled":     False,
        "securityEnabled": True,
    }

    if description:
        payload["description"] = description

    # Add devices as members using their Azure AD object IDs
    if device_ids:
        payload["members@odata.bind"] = [
            f"https://graph.microsoft.com/v1.0/directoryObjects/{did}"
            for did in device_ids
        ]

    print(f"\nCreating device group '{display_name}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! Device group created.")
        print(f"Name:     {data.get('displayName')}")
        print(f"Group ID: {data.get('id')}")
        if device_ids:
            print(f"Devices:  {len(device_ids)} added")
        print(f"\nTip: Assign Intune policies to this group to target specific devices.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_device_group()
    except Exception as e:
        print(f"Critical error: {e}")
