import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def delete_tap():
    """
    Deletes a Temporary Access Pass for a user.
    Use this to revoke a TAP that was compromised or no longer needed.
    """
    print("\n=== Microsoft Graph: Delete Temporary Access Pass ===")

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

    # List existing TAPs
    response = requests.get(
        f"https://graph.microsoft.com/v1.0/users/{user_id}/authentication/temporaryAccessPassMethods",
        headers={"Authorization": f"Bearer {token}"}
    )

    taps = response.json().get("value", []) if response.status_code == 200 else []

    if not taps:
        print(f"\nNo active TAPs found for {user.get('displayName')}.")
        return

    print(f"\nActive TAPs for {user.get('displayName')}:")
    for i, tap in enumerate(taps, start=1):
        print(f"  {i}. ID: {tap.get('id')}  |  {tap.get('lifetimeInMinutes')} min  |  one-time: {tap.get('isUsableOnce')}")

    choice = input("\nEnter TAP number to delete: ").strip()
    try:
        tap = taps[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return

    confirm = input(f"\nDelete TAP '{tap.get('id')[:16]}...' for {upn}? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    del_resp = requests.delete(
        f"https://graph.microsoft.com/v1.0/users/{user_id}/authentication/temporaryAccessPassMethods/{tap['id']}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if del_resp.status_code == 204:
        print(f"\n✅ TAP deleted successfully.")
    else:
        print(f"\n❌ Failed (HTTP {del_resp.status_code}):")
        print(del_resp.text)

if __name__ == "__main__":
    try:
        delete_tap()
    except Exception as e:
        print(f"Critical error: {e}")
