import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import re
import requests
from core.auth import get_access_token

# ⚠️  Dynamic groups require Entra ID Premium P1 license
# Activate trial: Entra admin center → Licenses → All products → Try/Buy → Microsoft Entra ID P2

RULE_TEMPLATES = {
    "1": {
        "label": "All users in tenant",
        "rule":  'user.objectId -ne null'
    },
    "2": {
        "label": "Users with Intune license assigned",
        "rule":  'user.assignedPlans -any (assignedPlan.servicePlanId -eq "c1ec4a95-1f05-45b3-a911-aa3fa01094f5" -and assignedPlan.capabilityStatus -eq "Enabled")'
    },
    "3": {
        "label": "Users by department (you'll be prompted)",
        "rule":  None  # Will be filled in interactively
    },
    "4": {
        "label": "Users by job title (you'll be prompted)",
        "rule":  None
    },
    "5": {
        "label": "Custom rule (enter manually)",
        "rule":  None
    },
}

def generate_nickname(name: str) -> str:
    nickname = name.lower()
    nickname = re.sub(r'[^a-z0-9_]', '_', nickname)
    nickname = re.sub(r'_+', '_', nickname)
    return nickname.strip('_')[:64] or "group"

def create_dynamic_user_group():
    """
    Creates a dynamic Azure AD user group via Microsoft Graph API.

    ⚠️  REQUIRES: Entra ID Premium P1 or P2 license.
    Without Premium, the API will return 403.

    Dynamic membership rules automatically add/remove users based on
    their attributes (department, jobTitle, assignedLicenses, etc.)
    No manual member management needed.
    """
    print("\n=== Microsoft Graph: Create Dynamic User Group ===")
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
        dept = input("Enter department name: ").strip()
        rule = f'user.department -eq "{dept}"'
    elif choice == "4":
        title = input("Enter job title: ").strip()
        rule = f'user.jobTitle -eq "{title}"'
    elif choice == "5":
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
        "displayName":              display_name,
        "mailNickname":             mail_nickname,
        "groupTypes":               ["DynamicMembership"],
        "mailEnabled":              False,
        "securityEnabled":          True,
        "membershipRule":           rule,
        "membershipRuleProcessingState": "On",
    }

    if description:
        payload["description"] = description

    print(f"\nCreating dynamic user group '{display_name}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! Dynamic user group created.")
        print(f"Name:     {data.get('displayName')}")
        print(f"Group ID: {data.get('id')}")
        print(f"Rule:     {rule}")
        print(f"\nℹ️  Members will be automatically added/removed based on the rule.")
        print(f"Initial sync may take a few minutes.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        if response.status_code == 403:
            print("→ Entra ID Premium P1/P2 required for dynamic groups.")
            print("→ Activate trial: Entra admin center → Licenses → Try/Buy → Entra ID P2")
        print(response.text)

if __name__ == "__main__":
    try:
        create_dynamic_user_group()
    except Exception as e:
        print(f"Critical error: {e}")
