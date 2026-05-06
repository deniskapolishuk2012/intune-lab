import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def list_apps():
    """
    Lists all Win32 apps in Intune with their publishing state and assignments.
    """
    print("\n=== Microsoft Graph: List Win32 Apps ===")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    url     = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps?$filter=isof('microsoft.graph.win32LobApp')"

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed (HTTP {response.status_code}):")
        print(response.text)
        return

    apps = response.json().get("value", [])

    if not apps:
        print("\nNo Win32 apps found. Upload one with upload_win32_app.py.")
        return

    print(f"\nFound {len(apps)} Win32 app(s):\n")
    print(f"{'#':<4} {'App Name':<35} {'Publisher':<20} {'State':<15} {'ID'}")
    print("-" * 100)

    for i, a in enumerate(apps, start=1):
        print(
            f"{i:<4} {a.get('displayName','N/A'):<35} "
            f"{a.get('publisher','N/A'):<20} "
            f"{a.get('publishingState','N/A'):<15} "
            f"{a.get('id','N/A')}"
        )

if __name__ == "__main__":
    try:
        list_apps()
    except Exception as e:
        print(f"Critical error: {e}")
