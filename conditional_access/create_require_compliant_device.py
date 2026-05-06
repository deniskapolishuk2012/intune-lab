import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def create_require_compliant_device():
    """
    Creates a Conditional Access policy that requires a compliant device
    to access Microsoft 365 apps.

    Targets:
    - All users (excluding break-glass accounts if configured)

    Conditions:
    - Microsoft 365 apps (Exchange, SharePoint, Teams)
    - Windows, iOS, Android platforms

    Grant control:
    - Require device to be marked as compliant (Intune)

    ⚠️  Requires Entra ID Premium P1 license.
    Policy is created in REPORT-ONLY mode.
    """
    print("\n=== Create Conditional Access: Require Compliant Device for M365 ===")
    print("⚠️  Requires Entra ID Premium P1/P2.")
    print("ℹ️  Policy created in Report-Only mode — enable manually when ready.\n")

    name = input("Policy name [CA002 - Require Compliant Device for M365]: ").strip() or "CA002 - Require Compliant Device for M365"

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    payload = {
        "displayName": name,
        "state":       "enabledForReportingButNotEnforced",

        "conditions": {
            "users": {
                "includeUsers": ["All"],
                "excludeUsers": []  # Add break-glass account IDs here
            },
            "applications": {
                # Microsoft 365 core apps
                "includeApplications": [
                    "00000002-0000-0ff1-ce00-000000000000",  # Exchange Online
                    "00000003-0000-0ff1-ce00-000000000000",  # SharePoint Online
                    "cc15fd57-2c6c-4117-a88c-83b1d56b4bbe",  # Microsoft Teams
                ]
            },
            "platforms": {
                "includePlatforms": ["windows", "iOS", "android"]
            }
        },

        "grantControls": {
            "operator":        "OR",
            "builtInControls": ["compliantDevice"]  # Require Intune compliant device
        }
    }

    url     = "https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"Creating '{name}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! Conditional Access policy created.")
        print(f"Name:  {data.get('displayName')}")
        print(f"ID:    {data.get('id')}")
        print(f"State: {data.get('state')} (report-only)")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_require_compliant_device()
    except Exception as e:
        print(f"Critical error: {e}")
