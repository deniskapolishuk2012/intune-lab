import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def get_groups(token: str) -> list:
    """Fetches all Azure AD security groups."""
    url      = "https://graph.microsoft.com/v1.0/groups?$filter=securityEnabled eq true"
    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    return response.json().get("value", [])

def get_all_policies(token: str) -> list:
    """
    Fetches compliance policies and configuration profiles (includes update rings)
    and returns them as a unified list with type labels.
    """
    headers = {"Authorization": f"Bearer {token}"}
    all_policies = []

    sources = [
        {
            "label": "Compliance Policy",
            "url":   "https://graph.microsoft.com/v1.0/deviceManagement/deviceCompliancePolicies",
            "assign_url_tpl": "https://graph.microsoft.com/v1.0/deviceManagement/deviceCompliancePolicies/{id}/assign"
        },
        {
            "label": "Configuration Profile / Update Ring",
            "url":   "https://graph.microsoft.com/v1.0/deviceManagement/deviceConfigurations",
            "assign_url_tpl": "https://graph.microsoft.com/v1.0/deviceManagement/deviceConfigurations/{id}/assign"
        },
    ]

    for source in sources:
        response = requests.get(source["url"], headers=headers)
        if response.status_code != 200:
            continue
        for item in response.json().get("value", []):
            all_policies.append({
                "id":          item.get("id"),
                "name":        item.get("displayName", "N/A"),
                "type":        source["label"],
                "assign_url":  source["assign_url_tpl"].replace("{id}", item.get("id", ""))
            })

    return all_policies

def assign_policy():
    """
    Assigns an Intune policy (compliance, configuration profile, or update ring)
    to an Azure AD security group via Microsoft Graph API.
    """
    print("\n=== Microsoft Graph: Assign Policy to Group ===")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    # Pick policy
    print("\nFetching policies...")
    policies = get_all_policies(token)
    if not policies:
        print("❌ No policies found. Create one first.")
        return

    print(f"\n{'#':<4} {'Type':<35} {'Name'}")
    print("-" * 80)
    for i, p in enumerate(policies, start=1):
        print(f"{i:<4} {p['type']:<35} {p['name']}")

    choice = input("\nEnter policy number to assign: ").strip()
    try:
        policy = policies[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return

    # Pick group
    print("\nFetching security groups...")
    groups = get_groups(token)
    if not groups:
        print("❌ No security groups found. Create one first with create_group.py.")
        return

    print("\nAvailable groups:")
    for i, g in enumerate(groups, start=1):
        print(f"  {i}. {g.get('displayName','N/A')}")

    choice2 = input("\nEnter group number: ").strip()
    try:
        group = groups[int(choice2) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return

    # Assign
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }
    payload = {
        "assignments": [
            {
                "target": {
                    "@odata.type": "#microsoft.graph.groupAssignmentTarget",
                    "groupId":     group["id"]
                }
            }
        ]
    }

    print(f"\nAssigning '{policy['name']}' → '{group.get('displayName')}'...")
    response = requests.post(policy["assign_url"], json=payload, headers=headers)

    if response.status_code in (200, 201):
        print(f"\n✅ Success! Policy assigned to group '{group.get('displayName')}'.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        assign_policy()
    except Exception as e:
        print(f"Critical error: {e}")