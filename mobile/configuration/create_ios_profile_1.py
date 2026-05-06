import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import requests
from core.auth import get_access_token

TEMPLATES = {
    "1": {
        "label": "Device Restrictions — block camera, screenshots, iCloud",
        "payload": {
            "@odata.type":                         "#microsoft.graph.iosGeneralDeviceConfiguration",
            "cameraBlocked":                        True,   # Block camera
            "screenCaptureBlocked":                 True,   # Block screenshots
            "iCloudBlockBackup":                    True,   # Block iCloud backup
            "iCloudBlockDocumentSync":              True,   # Block iCloud doc sync
            "iCloudBlockPhotoLibrary":              True,   # Block iCloud photos
            "airDropBlocked":                       True,   # Block AirDrop
            "iTunesBlocked":                        True,   # Block iTunes
            "safariBlocked":                        False,  # Allow Safari
            "siriBlocked":                          False,  # Allow Siri
            "diagnosticDataSubmissionBlocked":      True,   # Block diagnostic data
        }
    },
    "2": {
        "label": "Email & Wi-Fi baseline — corporate mail config",
        "payload": {
            "@odata.type":                    "#microsoft.graph.iosGeneralDeviceConfiguration",
            "airDropBlocked":                  True,
            "diagnosticDataSubmissionBlocked": True,
            "iCloudBlockBackup":               False,  # Allow backup for corporate
            "screenCaptureBlocked":            True,
            "cameraBlocked":                   False,  # Allow camera
        }
    },
}

def create_ios_profile():
    """
    Creates an iOS/iPadOS configuration profile in Intune via Microsoft Graph API.

    Uses legacy /deviceConfigurations endpoint (iosGeneralDeviceConfiguration).
    Covers device restrictions: camera, screenshots, iCloud, AirDrop.
    """
    print("\n=== Create iOS Configuration Profile ===")

    name = input("Profile name [iOS - Device Restrictions]: ").strip() or "iOS - Device Restrictions"
    desc = input("Description (optional): ").strip() or "iOS device restrictions"

    print("\nSelect template:")
    for key, t in TEMPLATES.items():
        print(f"  {key}. {t['label']}")

    choice = input("\nEnter template number [1]: ").strip() or "1"
    if choice not in TEMPLATES:
        print("❌ Invalid choice.")
        return

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    payload = TEMPLATES[choice]["payload"].copy()
    payload["displayName"] = name
    if desc:
        payload["description"] = desc

    url     = "https://graph.microsoft.com/v1.0/deviceManagement/deviceConfigurations"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\nCreating '{name}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! iOS Configuration Profile created.")
        print(f"Name: {data.get('displayName')}")
        print(f"ID:   {data.get('id')}")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_ios_profile()
    except Exception as e:
        print(f"Critical error: {e}")
