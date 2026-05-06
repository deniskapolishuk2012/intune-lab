import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def create_block_legacy_auth():
    """
    Creates a Conditional Access policy that blocks legacy authentication protocols.

    Legacy auth (Basic Auth, SMTP AUTH, POP3, IMAP) bypasses MFA completely —
    this is one of the most common attack vectors for credential stuffing.

    Targets:
    - All users

    Conditions:
    - All cloud apps
    - Legacy authentication clients only

    Grant control:
    - Block access

    ⚠️  Requires Entra ID Premium P1 license.
    Policy is created in REPORT-ONLY mode — check impact before enabling.
    """
    print("\n=== Create Conditional Access: Block Legacy Authentication ===")
    print("⚠️  Requires Entra ID Premium P1/P2.")
    print("ℹ️  Policy created in Report-Only mode.")
    print("ℹ️  Check Sign-in logs for legacy auth usage before enabling!\n")

    name = input("Policy name [CA003 - Block Legacy Authentication]: ").strip() or "CA003 - Block Legacy Authentication"

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    payload = {
        "displayName": name,
        "state":       "enabledForReportingButNotEnforced",

        "conditions": {
            "users": {
                "includeUsers": ["All"]
            },
            "applications": {
                "includeApplications": ["All"]
            },
            "clientAppTypes": [
                "exchangeActiveSync",       # Exchange ActiveSync (older Outlook)
                "other"                     # Other legacy clients (IMAP, POP3, SMTP)
            ]
        },

        "grantControls": {
            "operator":        "OR",
            "builtInControls": ["block"]   # Block access completely
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
        print(f"\n⚠️  Before enabling: check Entra Sign-in logs for legacy auth usage.")
        print(f"   Enabling without checking may break older mail clients.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_block_legacy_auth()
    except Exception as e:
        print(f"Critical error: {e}")
