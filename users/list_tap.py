import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def list_tap():
    """
    Lists active Temporary Access Passes for a user.
    Shows TAP ID, lifetime, one-time flag, and expiry.
    """
    print("\n=== Microsoft Graph: List Temporary Access Passes ===")

    upn = input("Enter user UPN: ").strip()

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    user_resp = requests.get(
        f"https://graph.microsoft.com/v1.0/users/{upn}?$select=id,displayName",
        headers={"Authorization": f"Bearer {token}"}
    )
    if user_resp.status_code != 200:
        print(f"❌ User '{upn}' not found.")
        return

    user    = user_resp.json()
    user_id = user.get("id")

    response = requests.get(
        f"https://graph.microsoft.com/v1.0/users/{user_id}/authentication/temporaryAccessPassMethods",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        print(f"❌ Failed (HTTP {response.status_code}):")
        print(response.text)
        return

    taps = response.json().get("value", [])

    if not taps:
        print(f"\nNo active TAPs found for {user.get('displayName')}.")
        return

    print(f"\nActive TAPs for {user.get('displayName')} ({upn}):\n")
    print(f"{'#':<4} {'ID':<40} {'Lifetime':<12} {'One-Time':<12} {'Start'}")
    print("-" * 90)

    for i, tap in enumerate(taps, start=1):
        print(
            f"{i:<4} {tap.get('id','N/A'):<40} "
            f"{str(tap.get('lifetimeInMinutes','N/A')) + ' min':<12} "
            f"{str(tap.get('isUsableOnce','N/A')):<12} "
            f"{tap.get('startDateTime','N/A')}"
        )

if __name__ == "__main__":
    try:
        list_tap()
    except Exception as e:
        print(f"Critical error: {e}")
