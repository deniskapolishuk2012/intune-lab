import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def create_tap():
    """
    Creates a Temporary Access Pass (TAP) for a user via Microsoft Graph API.

    TAP is a time-limited passcode that allows users to:
    - Sign in without a password (passwordless onboarding)
    - Register new MFA methods (authenticator app, FIDO2 key)
    - Recover access when MFA device is lost

    Common use cases:
    - New employee onboarding → give TAP instead of temporary password
    - User lost phone → give TAP to re-register authenticator
    - Passwordless bootstrap → first-time FIDO2 key registration

    ⚠️  Requires Entra ID Premium P1/P2 and TAP policy enabled in tenant.
    """
    print("\n=== Microsoft Graph: Create Temporary Access Pass (TAP) ===")
    print("ℹ️  TAP allows passwordless sign-in for onboarding or MFA recovery.\n")

    upn = input("Enter user UPN: ").strip()

    print("\nTAP lifetime:")
    print("  1. 1 hour   — for quick onboarding sessions")
    print("  2. 4 hours  — standard (recommended)")
    print("  3. 8 hours  — for extended setup sessions")
    print("  4. Custom   — enter minutes manually")

    lifetime_map = {"1": 60, "2": 240, "3": 480}
    choice = input("\nEnter number [2]: ").strip() or "2"

    if choice == "4":
        try:
            lifetime = int(input("Enter lifetime in minutes (1-43200): ").strip())
        except ValueError:
            lifetime = 240
    else:
        lifetime = lifetime_map.get(choice, 240)

    one_time = input("\nOne-time use only? (y = one-time, n = reusable within lifetime) [y]: ").strip().lower()
    is_one_time = one_time != "n"

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    # First resolve UPN to user ID
    user_resp = requests.get(
        f"https://graph.microsoft.com/v1.0/users/{upn}?$select=id,displayName",
        headers={"Authorization": f"Bearer {token}"}
    )
    if user_resp.status_code != 200:
        print(f"❌ User '{upn}' not found.")
        return

    user    = user_resp.json()
    user_id = user.get("id")

    payload = {
        "lifetimeInMinutes": lifetime,
        "isUsableOnce":      is_one_time,
    }

    url     = f"https://graph.microsoft.com/v1.0/users/{user_id}/authentication/temporaryAccessPassMethods"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\nCreating TAP for '{user.get('displayName')}' ({upn})...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! Temporary Access Pass created.")
        print(f"User:        {user.get('displayName')}")
        print(f"TAP:         {data.get('temporaryAccessPass')}")
        print(f"Valid for:   {data.get('lifetimeInMinutes')} minutes")
        print(f"One-time:    {data.get('isUsableOnce')}")
        print(f"Starts at:   {data.get('startDateTime')}")
        print(f"\n⚠️  Share this TAP securely — treat it like a password.")
        print(f"   User should register MFA methods immediately after sign-in.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)
        if response.status_code == 404:
            print("\nℹ️  TAP may not be enabled in your tenant.")
            print("   Enable it: Entra portal → Protection → Authentication methods → Temporary Access Pass")

if __name__ == "__main__":
    try:
        create_tap()
    except Exception as e:
        print(f"Critical error: {e}")
