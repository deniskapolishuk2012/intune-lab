import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import json
import requests
from core.auth import get_access_token

TEMPLATES = {
    "1": {
        "label": "Standard User — user-driven AAD join",
        "oobe": {
            "hidePrivacySettings": True,
            "hideEULA":            True,
            "userType":            "administrator",
        }
    },
    "2": {
        "label": "Admin / Privileged — all screens hidden",
        "oobe": {
            "hidePrivacySettings": True,
            "hideEULA":            True,
            "userType":            "administrator",
        }
    },
}

def create_deployment_profile():
    print("\n=== Microsoft Graph: Create Autopilot Deployment Profile ===")

    name = input("Profile name [Autopilot Profile]: ").strip() or "Autopilot Profile"
    desc = input("Description (optional): ").strip() or ""

    print("\nSelect template:")
    for key, t in TEMPLATES.items():
        print(f"  {key}. {t['label']}")

    choice = input("\nEnter template number [1]: ").strip() or "1"
    if choice not in TEMPLATES:
        print("❌ Invalid choice.")
        return

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    payload = {
        "@odata.type":               "#microsoft.graph.azureADWindowsAutopilotDeploymentProfile",
        "displayName":                name,
        "outOfBoxExperienceSettings": TEMPLATES[choice]["oobe"],
    }
    if desc:
        payload["description"] = desc

    print(f"\nPayload being sent:")
    print(json.dumps(payload, indent=2))

    url     = "https://graph.microsoft.com/beta/deviceManagement/windowsAutopilotDeploymentProfiles"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\nCreating '{name}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success!")
        print(f"Name: {data.get('displayName')}")
        print(f"ID:   {data.get('id')}")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_deployment_profile()
    except Exception as e:
        print(f"Critical error: {e}")
