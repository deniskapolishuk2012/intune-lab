import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import requests
from core.auth import get_access_token

RINGS = {
    "1": {
        "label": "Pilot Ring — fast updates (IT / test group)",
        "qualityDeferral": 0,
        "featureDeferral": 0,
        "autoUpdate":      "autoInstallAndRebootWithoutEndUserControl",
        "installDay":      "sunday",
        "installTime":     2,
    },
    "2": {
        "label": "Standard Ring — 7 day quality / 30 day feature deferral",
        "qualityDeferral": 7,
        "featureDeferral": 30,
        "autoUpdate":      "autoInstallAndRebootAtScheduledTime",
        "installDay":      "sunday",
        "installTime":     3,
    },
    "3": {
        "label": "Broad Ring — 14 day quality / 60 day feature deferral",
        "qualityDeferral": 14,
        "featureDeferral": 60,
        "autoUpdate":      "autoInstallAndRebootAtScheduledTime",
        "installDay":      "sunday",
        "installTime":     3,
    },
}

def create_update_ring():
    """
    Creates a Windows Update Ring via legacy /deviceConfigurations API.
    Update Rings are NOT in Settings Catalog — they use the Templates API.

    Three ring options:
    - Pilot:    No deferral — updates install immediately (for IT/test devices)
    - Standard: 7/30 day deferral — for most users
    - Broad:    14/60 day deferral — for critical/stable devices
    """
    print("\n=== Create Profile: Windows Update Ring ===")
    print("ℹ️  Update Rings use the Templates API (/deviceConfigurations), not Settings Catalog.\n")

    name = input("Profile name [Windows - Update Ring Standard]: ").strip() or "Windows - Update Ring Standard"
    desc = input("Description [Windows Update Ring]: ").strip() or "Windows Update Ring"

    print("\nSelect ring type:")
    for key, r in RINGS.items():
        print(f"  {key}. {r['label']}")

    choice = input("\nEnter ring number [2]: ").strip() or "2"
    if choice not in RINGS:
        print("❌ Invalid choice.")
        return

    ring = RINGS[choice]

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    payload = {
        "@odata.type":                                "#microsoft.graph.windowsUpdateForBusinessConfiguration",
        "displayName":                                 name,
        "description":                                 desc,
        "businessReadyUpdatesOnly":                    "businessReadyOnly",
        "automaticUpdateMode":                         ring["autoUpdate"],
        "microsoftUpdateServiceAllowed":               True,
        "driversExcluded":                             False,
        "qualityUpdatesDeferralPeriodInDays":          ring["qualityDeferral"],
        "featureUpdatesDeferralPeriodInDays":          ring["featureDeferral"],
        "featureUpdatesRollbackWindowInDays":          10,
        "scheduledInstallDay":                         ring["installDay"],
        "scheduledInstallTime":                        ring["installTime"],
        "userPauseAccess":                             "disabled",
        "userWindowsUpdateScanAccess":                 "disabled",
        "updateNotificationLevel":                     "defaultNotifications",
    }

    url     = "https://graph.microsoft.com/v1.0/deviceManagement/deviceConfigurations"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\nCreating '{name}' ({ring['label']})...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! Update Ring created.")
        print(f"Name:             {data.get('displayName')}")
        print(f"ID:               {data.get('id')}")
        print(f"Quality deferral: {ring['qualityDeferral']} days")
        print(f"Feature deferral: {ring['featureDeferral']} days")
        print(f"Install schedule: {ring['installDay'].capitalize()} at 0{ring['installTime']}:00")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_update_ring()
    except Exception as e:
        print(f"Critical error: {e}")
