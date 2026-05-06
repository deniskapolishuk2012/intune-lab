import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def create_require_mfa_admins():
    """
    Creates a Conditional Access policy that requires MFA for admin roles.

    Targets:
    - Global Administrator, Security Administrator, Intune Administrator,
      Conditional Access Administrator, Cloud Application Administrator

    Conditions:
    - All cloud apps
    - All platforms

    Grant control:
    - Require MFA

    ⚠️  Requires Entra ID Premium P1 license.
    Policy is created in REPORT-ONLY mode — safe to test before enabling.
    """
    print("\n=== Create Conditional Access: Require MFA for Admins ===")
    print("⚠️  Requires Entra ID Premium P1/P2.")
    print("ℹ️  Policy created in Report-Only mode — enable manually when ready.\n")

    name = input("Policy name [CA001 - Require MFA for Admins]: ").strip() or "CA001 - Require MFA for Admins"

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    payload = {
        "displayName": name,
        "state":       "enabledForReportingButNotEnforced",  # Report-only — safe default

        "conditions": {
            "users": {
                # Target all users with admin roles
                "includeRoles": [
                    "62e90394-69f5-4237-9190-012177145e10",  # Global Administrator
                    "194ae4cb-b126-40b2-bd5b-6091b380977d",  # Security Administrator
                    "3a2c62db-5318-420d-8d74-23affee5d9d5",  # Intune Administrator
                    "b1be1c3e-b65d-4f19-8427-f6fa0d97feb9",  # Conditional Access Administrator
                    "158c047a-c907-4556-b7ef-446551a6b5f7",  # Cloud Application Administrator
                ]
            },
            "applications": {
                "includeApplications": ["All"]  # All cloud apps
            },
            "platforms": {
                "includePlatforms": ["all"]
            },
            "locations": {
                "includeLocations": ["All"]
            }
        },

        "grantControls": {
            "operator":        "OR",
            "builtInControls": ["mfa"]  # Require MFA
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
        print(f"\nTo enable: change state to 'enabled' in Entra portal or use update script.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_require_mfa_admins()
    except Exception as e:
        print(f"Critical error: {e}")
