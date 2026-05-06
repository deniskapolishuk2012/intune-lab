import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def licensed_users_report():
    """
    Reports all users in the tenant with their assigned licenses.
    Shows:
    - Users WITH licenses (which SKUs)
    - Users WITHOUT any license assigned
    Useful for license hygiene and identifying unlicensed accounts.
    """
    print("\n=== Report: Licensed Users ===")

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Fetch all users with license details
    url = (
        "https://graph.microsoft.com/v1.0/users"
        "?$select=displayName,userPrincipalName,assignedLicenses,accountEnabled"
        "&$top=999"
    )

    all_users = []
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed (HTTP {response.status_code}):")
            print(response.text)
            return
        data     = response.json()
        all_users.extend(data.get("value", []))
        url = data.get("@odata.nextLink")  # Handle pagination

    # Fetch SKU names for mapping
    sku_map = {}
    sku_response = requests.get("https://graph.microsoft.com/v1.0/subscribedSkus", headers=headers)
    if sku_response.status_code == 200:
        for sku in sku_response.json().get("value", []):
            sku_map[sku["skuId"]] = sku.get("skuPartNumber", sku["skuId"])

    licensed   = [u for u in all_users if u.get("assignedLicenses")]
    unlicensed = [u for u in all_users if not u.get("assignedLicenses")]

    print(f"\nTotal users: {len(all_users)}")
    print(f"  ✅ Licensed:   {len(licensed)}")
    print(f"  ⚠️  Unlicensed: {len(unlicensed)}")

    # Licensed users
    if licensed:
        print(f"\n--- Licensed Users ---")
        print(f"{'#':<4} {'Display Name':<25} {'UPN':<40} {'Enabled':<10} {'Licenses'}")
        print("-" * 110)
        for i, u in enumerate(licensed, start=1):
            license_names = ", ".join(
                sku_map.get(lic["skuId"], lic["skuId"])
                for lic in u.get("assignedLicenses", [])
            )
            enabled = "Yes" if u.get("accountEnabled") else "No"
            print(
                f"{i:<4} {u.get('displayName','N/A'):<25} "
                f"{u.get('userPrincipalName','N/A'):<40} "
                f"{enabled:<10} {license_names}"
            )

    # Unlicensed users
    if unlicensed:
        print(f"\n--- Unlicensed Users ---")
        print(f"{'#':<4} {'Display Name':<25} {'UPN':<40} {'Enabled'}")
        print("-" * 85)
        for i, u in enumerate(unlicensed, start=1):
            enabled = "Yes" if u.get("accountEnabled") else "No"
            print(
                f"{i:<4} {u.get('displayName','N/A'):<25} "
                f"{u.get('userPrincipalName','N/A'):<40} "
                f"{enabled}"
            )
        print(f"\nTip: Use assign_license.py to assign licenses to unlicensed users.")

if __name__ == "__main__":
    try:
        licensed_users_report()
    except Exception as e:
        print(f"Critical error: {e}")
