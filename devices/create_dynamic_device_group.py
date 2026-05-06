import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import re
import requests
from core.auth import get_access_token

# ⚠️  Dynamic groups require Entra ID Premium P1 license

RULE_TEMPLATES = {
    "1": {
        "label": "All Windows devices",
        "rule":  '(device.deviceOSType -eq "Windows")'
    },
    "2": {
        "label": "All Intune managed devices",
        "rule":  '(device.deviceManagementAppId -eq "0000000a-0000-0000-c000-000000000000")'
    },
    "3": {
        "label": "Devices by OS version (you'll be prompted)",
        "rule":  None
    },
    "4": {
        "label": "Devices by display name prefix (you'll be prompted)",
        "rule":  None
    },
    "5": {
        "label": "Autopilot devices (by enrollmentProfileName)",
        "rule":  None
    },
    "6": {
        "label": "Custom rule (enter manually)",
        "rule":  None
    },
}

def generate_nickname(name: str) -> str:
    nickname = name.lower()
    nickname = re.sub(r'[^a-z0-9_]', '_', nickname)
    nickname = re.sub(r'_+', '_', nickname)
    return nickname.strip('_')[:64] or "group"

def create_dynamic_device_group():
    """
    Creates a dynamic Azure AD device group via Microsoft Graph API.

    ⚠️  REQUIRES: Entra ID Premium P1 or P2 license.

    Dynamic device groups are very useful for Autopilot and Intune:
    - Automatically target all Windows devices
    - Automatically target devices enrolled via specific Autopilot profile
    - Target devices by OS version for staged rollouts
    """
    print("\n=== Microsoft Graph: Create Dynamic Device Group ===")
    print("⚠️  Requires Entra ID Premium P1/P2 license.\n")

    display_name  = input("Group name: ").strip()
    auto_nickname = generate_nickname(display_name)
    mail_nickname = input(f"Mail nickname [{auto_nickname}]: ").strip().replace(" ", "_") or auto_nickname
    description   = input("Description (optional): ").strip()

    print("\nSelect membership rule:")
    for key, t in RULE_TEMPLATES.items():
        print(f"  {key}. {t['label']}")

    choice = input("\nEnter template number: ").strip()
    if choice not in RULE_TEMPLATES:
        print("❌ Invalid choice.")
        return

    rule = RULE_TEMPLATES[choice]["rule"]

    if choice == "3":
        version = input("Enter OS version (e.g. 10.0.19045): ").strip()
        rule = f'(device.deviceOSVersion -startsWith "{version}")'
    elif choice == "4":
        prefix = input("Enter device name prefix (e.g. DESKTOP-): ").strip()
        rule = f'(device.displayName -startsWith "{prefix}")'
    elif choice == "5":
        profile = input("Enter Autopilot enrollment profile name: ").strip()
        rule = f'(device.enrollmentProfileName -eq "{profile}")'
    elif choice == "6":
        rule = input("Enter custom membership rule: ").strip()

    if not rule:
        print("❌ No rule specified.")
        return

    print(f"\nMembership rule: {rule}")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    url     = "https://graph.microsoft.com/v1.0/groups"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    payload = {
        "displayName":                   display_name,
        "mailNickname":                  mail_nickname,
        "groupTypes":                    ["DynamicMembership"],
        "mailEnabled":                   False,
        "securityEnabled":               True,
        "membershipRule":                rule,
        "membershipRuleProcessingState": "On",
    }

    if description:
        payload["description"] = description

    print(f"\nCreating dynamic device group '{display_name}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! Dynamic device group created.")
        print(f"Name:     {data.get('displayName')}")
        print(f"Group ID: {data.get('id')}")
        print(f"Rule:     {rule}")
        print(f"\nℹ️  Devices matching the rule will be added automatically.")
        print(f"Assign Intune policies to this group to target matching devices.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        if response.status_code == 403:
            print("→ Entra ID Premium P1/P2 required for dynamic groups.")
            print("→ Activate trial: Entra admin center → Licenses → Try/Buy → Entra ID P2")
        print(response.text)

if __name__ == "__main__":
    try:
        create_dynamic_device_group()
    except Exception as e:
        print(f"Critical error: {e}")
