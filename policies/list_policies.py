import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def list_policies():
    """
    Lists all Intune policies in the tenant:
    - Compliance policies          (/deviceCompliancePolicies)
    - Settings Catalog profiles    (/beta/configurationPolicies)
    - Legacy configuration profiles (/deviceConfigurations — Update Rings etc.)
    - Win32 Apps                   (/mobileApps)
    """
    print("\n=== Microsoft Graph: List All Policies ===")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    sections = [
        {
            "label": "Compliance Policies",
            "url":   "https://graph.microsoft.com/v1.0/deviceManagement/deviceCompliancePolicies",
            "name_field": "displayName"
        },
        {
            "label": "Configuration Profiles (Settings Catalog)",
            "url":   "https://graph.microsoft.com/beta/deviceManagement/configurationPolicies",
            "name_field": "name"
        },
        {
            "label": "Configuration Profiles (Legacy / Update Rings)",
            "url":   "https://graph.microsoft.com/v1.0/deviceManagement/deviceConfigurations",
            "name_field": "displayName"
        },
        {
            "label": "Win32 Apps",
            "url":   "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps?$filter=isof('microsoft.graph.win32LobApp')",
            "name_field": "displayName"
        },
    ]

    for section in sections:
        print(f"\n--- {section['label']} ---")
        response = requests.get(section["url"], headers=headers)
        if response.status_code != 200:
            print(f"  ❌ Failed (HTTP {response.status_code})")
            continue

        items = response.json().get("value", [])
        if not items:
            print("  No items found.")
            continue

        name_field = section["name_field"]
        print(f"  {'#':<4} {'Name':<40} {'ID'}")
        print("  " + "-" * 80)
        for i, item in enumerate(items, start=1):
            name = item.get(name_field) or item.get("displayName") or "N/A"
            print(f"  {i:<4} {name:<40} {item.get('id','N/A')}")

if __name__ == "__main__":
    try:
        list_policies()
    except Exception as e:
        print(f"Critical error: {e}")
