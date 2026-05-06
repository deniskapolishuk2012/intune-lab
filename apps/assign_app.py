import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def get_apps(token: str) -> list:
    """Fetches all Win32 apps in Intune."""
    url     = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps?$filter=isof('microsoft.graph.win32LobApp')"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    return response.json().get("value", [])

def get_groups(token: str) -> list:
    """Fetches all security groups."""
    url     = "https://graph.microsoft.com/v1.0/groups?$filter=securityEnabled eq true"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    return response.json().get("value", [])

def assign_app():
    """
    Assigns a Win32 app to an Azure AD group via Microsoft Graph API.
    Assignment intents: required (force install), available (self-service), uninstall.
    """
    print("\n=== Microsoft Graph: Assign App to Group ===")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    # Pick app
    print("\nFetching Win32 apps...")
    apps = get_apps(token)
    if not apps:
        print("❌ No Win32 apps found. Upload one with upload_win32_app.py.")
        return

    print("\nAvailable apps:")
    for i, a in enumerate(apps, start=1):
        print(f"  {i}. {a.get('displayName','N/A')}  [{a.get('publishingState','N/A')}]")

    choice = input("\nEnter app number: ").strip()
    try:
        app = apps[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return

    # Pick group
    print("\nFetching security groups...")
    groups = get_groups(token)
    if not groups:
        print("❌ No groups found.")
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

    # Pick intent
    print("\nAssignment intent:")
    print("  1. Required     — force install on all devices in group")
    print("  2. Available    — appears in Company Portal (self-service)")
    print("  3. Uninstall    — force uninstall from devices in group")

    intent_map = {"1": "required", "2": "available", "3": "uninstall"}
    intent_choice = input("\nEnter intent [1]: ").strip() or "1"
    intent = intent_map.get(intent_choice, "required")

    app_id    = app.get("id")
    group_id  = group.get("id")
    app_name  = app.get("displayName")
    group_name = group.get("displayName")

    url = f"https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/{app_id}/assignments"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {
        "intent": intent,
        "target": {
            "@odata.type": "#microsoft.graph.groupAssignmentTarget",
            "groupId":     group_id
        },
        "settings": {
            "@odata.type":              "#microsoft.graph.win32LobAppAssignmentSettings",
            "notifications":             "showAll",
            "restartSettings":           None,
            "installTimeSettings":       None,
            "deliveryOptimizationPriority": "notConfigured"
        }
    }

    print(f"\nAssigning '{app_name}' → '{group_name}' (intent: {intent})...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code in (200, 201):
        print(f"\n✅ Success! App assigned.")
        print(f"App:    {app_name}")
        print(f"Group:  {group_name}")
        print(f"Intent: {intent}")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        assign_app()
    except Exception as e:
        print(f"Critical error: {e}")
