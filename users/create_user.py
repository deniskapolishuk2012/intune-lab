import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import CONFIG, get_access_token

def create_lab_user():
    """
    Interactively creates a new Azure AD user via Microsoft Graph API.
    """
    print("\n=== Microsoft Graph: Create User ===")

    display_name   = input("Enter full name (Display Name): ")
    login_nickname = input("Enter login nickname (e.g. denis_lab): ").strip().replace(" ", "")
    password       = input("Enter password for the new user: ")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    upn = f"{login_nickname}@{CONFIG['DOMAIN']}"

    payload = {
        "accountEnabled":    True,
        "displayName":       display_name,
        "mailNickname":      login_nickname,
        "userPrincipalName": upn,
        "usageLocation":     "IL",
        "passwordProfile": {
            "forceChangePasswordNextSignIn": False,
            "password": password
        }
    }

    url     = "https://graph.microsoft.com/v1.0/users"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\nCreating user {upn}...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! User created.")
        print(f"UPN:      {upn}")
        print(f"Password: {password}")
        print(f"ID:       {data.get('id')}")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_lab_user()
    except Exception as e:
        print(f"Critical error: {e}")
