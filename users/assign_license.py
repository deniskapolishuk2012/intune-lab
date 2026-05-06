import requests
from auth import get_access_token  # Import shared auth function

def get_available_skus(token: str) -> list:
    """
    Fetches all license SKUs available in the tenant.
    remaining = prepaidUnits.enabled - consumedUnits
    """
    url      = "https://graph.microsoft.com/v1.0/subscribedSkus"
    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Could not fetch SKUs (HTTP {response.status_code}): {response.text}")
        return []

    skus      = response.json().get("value", [])
    available = []
    for sku in skus:
        enabled   = sku.get("prepaidUnits", {}).get("enabled", 0)
        consumed  = sku.get("consumedUnits", 0)
        remaining = enabled - consumed
        available.append({
            "id":        sku["skuId"],
            "name":      sku.get("skuPartNumber", "Unknown"),
            "remaining": remaining,
            "total":     enabled
        })
    return available

def get_user_id(token: str, upn: str) -> str | None:
    """
    Resolves a UPN to an Azure AD object ID.
    Returns None if the user is not found.
    """
    url      = f"https://graph.microsoft.com/v1.0/users/{upn}"
    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("id")
    print(f"❌ User '{upn}' not found (HTTP {response.status_code}).")
    return None

def assign_license():
    """
    Interactively assigns a license to a user via Microsoft Graph API.
    Lists all SKUs from the tenant — no need to know GUIDs.
    """
    print("\n=== Microsoft Graph: Assign License to User ===")

    upn = input("Enter user UPN (e.g. denis_lab@contoso.onmicrosoft.com): ").strip()

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token. Check your Client ID and Secret.")
        return

    # Resolve user to object ID
    user_id = get_user_id(token, upn)
    if not user_id:
        return

    # Fetch SKUs
    print("\nFetching available licenses in your tenant...")
    skus = get_available_skus(token)
    if not skus:
        print("❌ No licenses found in your tenant.")
        return

    print("\nAvailable licenses:")
    for i, sku in enumerate(skus, start=1):
        print(f"  {i}. {sku['name']}  (available: {sku['remaining']} / {sku['total']})")

    choice = input("\nEnter the number of the license to assign: ").strip()
    try:
        selected = skus[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return

    # Assign license
    url     = f"https://graph.microsoft.com/v1.0/users/{user_id}/assignLicense"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }
    payload = {
        "addLicenses":    [{"skuId": selected["id"]}],
        "removeLicenses": []
    }

    print(f"\nAssigning '{selected['name']}' to {upn}...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print(f"\n✅ Success! License '{selected['name']}' assigned to {upn}.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        assign_license()
    except Exception as e:
        print(f"Critical error: {e}")
