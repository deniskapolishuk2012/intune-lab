import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def list_ca_policies():
    """
    Lists all Conditional Access policies in the tenant.
    Shows name, state, and creation date.
    """
    print("\n=== Microsoft Graph: List Conditional Access Policies ===")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        "https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed (HTTP {response.status_code}):")
        print(response.text)
        return

    policies = response.json().get("value", [])

    if not policies:
        print("\nNo Conditional Access policies found.")
        print("ℹ️  Requires Entra ID Premium P1/P2 to create policies.")
        return

    print(f"\nFound {len(policies)} CA policy/policies:\n")
    print(f"{'#':<4} {'Name':<45} {'State':<35} {'ID'}")
    print("-" * 110)

    state_labels = {
        "enabled":                              "🟢 Enabled",
        "disabled":                             "⚫ Disabled",
        "enabledForReportingButNotEnforced":    "🟡 Report-Only",
    }

    for i, p in enumerate(policies, start=1):
        state = state_labels.get(p.get("state", ""), p.get("state", "N/A"))
        print(f"{i:<4} {p.get('displayName','N/A'):<45} {state:<35} {p.get('id','N/A')}")

if __name__ == "__main__":
    try:
        list_ca_policies()
    except Exception as e:
        print(f"Critical error: {e}")
