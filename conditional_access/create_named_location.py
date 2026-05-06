import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

# Common country codes
COUNTRY_PRESETS = {
    "1": {"label": "Israel office",       "countries": ["IL"]},
    "2": {"label": "Israel + US",         "countries": ["IL", "US"]},
    "3": {"label": "EU countries",        "countries": ["IL", "DE", "FR", "GB", "NL", "PL"]},
    "4": {"label": "Custom (enter below)", "countries": []},
}

def create_named_location():
    """
    Creates a Named Location (country-based) in Entra ID.

    Named Locations are used in Conditional Access policies to:
    - Allow access only from trusted countries
    - Block access from high-risk regions
    - Reduce MFA requirements when signing in from known locations

    ⚠️  Requires Entra ID Premium P1 license.
    """
    print("\n=== Create Named Location (Country-based) ===")
    print("⚠️  Requires Entra ID Premium P1/P2.\n")

    name = input("Location name [Corporate Trusted Countries]: ").strip() or "Corporate Trusted Countries"

    print("\nSelect country preset:")
    for key, p in COUNTRY_PRESETS.items():
        countries_str = ", ".join(p["countries"]) if p["countries"] else "enter manually"
        print(f"  {key}. {p['label']} [{countries_str}]")

    choice = input("\nEnter preset number [1]: ").strip() or "1"
    if choice not in COUNTRY_PRESETS:
        print("❌ Invalid choice.")
        return

    if choice == "4":
        raw      = input("Enter country codes separated by comma (e.g. IL,US,DE): ").strip()
        countries = [c.strip().upper() for c in raw.split(",") if c.strip()]
    else:
        countries = COUNTRY_PRESETS[choice]["countries"]

    if not countries:
        print("❌ No countries specified.")
        return

    is_trusted = input("Mark as trusted location? [Y/n]: ").strip().lower()
    trusted    = is_trusted != "n"

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    payload = {
        "@odata.type":     "#microsoft.graph.countryNamedLocation",
        "displayName":      name,
        "countriesAndRegions": countries,
        "includeUnknownCountriesAndRegions": False,
        "isTrusted":        trusted
    }

    url     = "https://graph.microsoft.com/v1.0/identity/conditionalAccess/namedLocations"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\nCreating named location '{name}' with countries: {', '.join(countries)}...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! Named Location created.")
        print(f"Name:      {data.get('displayName')}")
        print(f"ID:        {data.get('id')}")
        print(f"Countries: {', '.join(data.get('countriesAndRegions', []))}")
        print(f"Trusted:   {data.get('isTrusted')}")
        print(f"\nTip: Use this location ID in CA policies to restrict access by geography.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_named_location()
    except Exception as e:
        print(f"Critical error: {e}")
