import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def enable_ca_policy():
    """
    Changes the state of a Conditional Access policy.
    Options: enabled, disabled, report-only

    Use this after verifying report-only mode shows no unintended blocks.
    """
    print("\n=== Change Conditional Access Policy State ===")

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
        print(f"❌ Failed to fetch policies (HTTP {response.status_code}):")
        print(response.text)
        return

    policies = response.json().get("value", [])
    if not policies:
        print("❌ No CA policies found.")
        return

    state_labels = {
        "enabled":                           "🟢 Enabled",
        "disabled":                          "⚫ Disabled",
        "enabledForReportingButNotEnforced": "🟡 Report-Only",
    }

    print("\nAvailable policies:")
    for i, p in enumerate(policies, start=1):
        state = state_labels.get(p.get("state", ""), p.get("state"))
        print(f"  {i}. {p.get('displayName','N/A'):<45} {state}")

    choice = input("\nEnter policy number: ").strip()
    try:
        policy = policies[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return

    print(f"\nChange state for: '{policy.get('displayName')}'")
    print(f"Current state: {state_labels.get(policy.get('state'), policy.get('state'))}")
    print(f"\nNew state:")
    print(f"  1. 🟢 Enabled       — enforce the policy")
    print(f"  2. 🟡 Report-Only   — log only, don't block")
    print(f"  3. ⚫ Disabled      — turn off completely")

    state_map = {
        "1": "enabled",
        "2": "enabledForReportingButNotEnforced",
        "3": "disabled"
    }

    state_choice = input("\nEnter number: ").strip()
    if state_choice not in state_map:
        print("❌ Invalid choice.")
        return

    new_state = state_map[state_choice]

    if new_state == "enabled":
        confirm = input(f"\n⚠️  Enable '{policy.get('displayName')}'? This will enforce the policy. [y/N]: ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return

    patch_url = f"https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies/{policy['id']}"
    resp = requests.patch(
        patch_url,
        json={"state": new_state},
        headers={**headers, "Content-Type": "application/json"}
    )

    if resp.status_code in (200, 204):
        print(f"\n✅ Policy state updated.")
        print(f"Policy: {policy.get('displayName')}")
        print(f"State:  {state_labels.get(new_state, new_state)}")
    else:
        print(f"\n❌ Failed (HTTP {resp.status_code}):")
        print(resp.text)

if __name__ == "__main__":
    try:
        enable_ca_policy()
    except Exception as e:
        print(f"Critical error: {e}")
