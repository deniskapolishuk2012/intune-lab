import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import re
import requests
from core.auth import get_access_token

def generate_nickname(name: str) -> str:
    """Generates a valid mail nickname from group display name."""
    nickname = name.lower()
    nickname = re.sub(r'[^a-z0-9_]', '_', nickname)  # Replace invalid chars with _
    nickname = re.sub(r'_+', '_', nickname)            # Collapse multiple underscores
    nickname = nickname.strip('_')[:64]                # Max 64 chars
    return nickname or "group"

def get_user_id(token: str, upn: str) -> str | None:
    """Resolves a UPN to an Azure AD object ID."""
    url      = f"https://graph.microsoft.com/v1.0/users/{upn}"
    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("id")
    print(f"  ⚠️  User '{upn}' not found (HTTP {response.status_code}). Skipping.")
    return None

def create_group():
    """
    Interactively creates a new Azure AD security group via Microsoft Graph API.
    Optionally adds existing users as members immediately upon creation.
    """
    print("\n=== Microsoft Graph: Create Security Group ===")

    display_name = input("Group name: ").strip()

    auto_nickname = generate_nickname(display_name)
    mail_nickname = input(f"Mail nickname [{auto_nickname}]: ").strip().replace(" ", "_")
    if not mail_nickname:
        mail_nickname = auto_nickname

    description = input("Description (optional): ").strip()

    print("\nAdd members now? Enter UPNs one by one, empty line to finish.")
    upns = []
    while True:
        upn = input(f"  UPN #{len(upns)+1} (or Enter to finish): ").strip()
        if not upn:
            break
        upns.append(upn)

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    member_ids = []
    if upns:
        print("\nResolving users...")
        for upn in upns:
            uid = get_user_id(token, upn)
            if uid:
                member_ids.append(uid)
                print(f"  ✅ Found: {upn}")

    url     = "https://graph.microsoft.com/v1.0/groups"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    payload = {
        "displayName":     display_name,
        "mailNickname":    mail_nickname,
        "groupTypes":      [],
        "mailEnabled":     False,
        "securityEnabled": True,
    }

    if description:
        payload["description"] = description

    if member_ids:
        payload["members@odata.bind"] = [
            f"https://graph.microsoft.com/v1.0/directoryObjects/{uid}"
            for uid in member_ids
        ]

    print(f"\nCreating group '{display_name}' (nickname: {mail_nickname})...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! Group created.")
        print(f"Name:     {data.get('displayName')}")
        print(f"Group ID: {data.get('id')}")
        if member_ids:
            print(f"Members:  {len(member_ids)} added")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_group()
    except Exception as e:
        print(f"Critical error: {e}")
