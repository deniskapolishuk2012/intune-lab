import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import requests
from core.auth import get_access_token

TEMPLATES = {
    "1": {
        "label": "Device Restrictions — block camera, screenshots, USB",
        "payload": {
            "@odata.type":                             "#microsoft.graph.androidGeneralDeviceConfiguration",
            "cameraBlocked":                            True,   # Block camera
            "screenCaptureBlocked":                     True,   # Block screenshots
            "googleAccountBlockAutoSync":               True,   # Block Google account sync
            "googlePlayStoreBlocked":                   False,  # Allow Play Store
            "webBrowserBlocked":                        False,  # Allow browser
            "appsBlockClipboardSharing":                True,   # Block clipboard
            "appsBlockCopyPaste":                       False,
            "bluetoothBlocked":                         False,
            "cellularBlockDataRoaming":                 True,   # Block roaming
            "diagnosticDataBlockSubmission":            True,
            "locationServicesBlocked":                  False,
            "nfcBlocked":                               True,   # Block NFC
            "passwordBlockFingerprintUnlock":           False,  # Allow fingerprint
            "usbMassStorageBlocked":                    True,   # Block USB storage
        }
    },
    "2": {
        "label": "BYOD restrictions — minimal controls for personal devices",
        "payload": {
            "@odata.type":                  "#microsoft.graph.androidGeneralDeviceConfiguration",
            "cameraBlocked":                 False,
            "screenCaptureBlocked":          True,
            "googleAccountBlockAutoSync":    False,
            "appsBlockClipboardSharing":     True,
            "cellularBlockDataRoaming":      False,
            "usbMassStorageBlocked":         True,
            "diagnosticDataBlockSubmission": True,
        }
    },
}

def create_android_profile():
    """
    Creates an Android configuration profile in Intune via Microsoft Graph API.

    Uses legacy /deviceConfigurations endpoint (androidGeneralDeviceConfiguration).
    Covers device restrictions: camera, screenshots, USB, NFC, clipboard.
    """
    print("\n=== Create Android Configuration Profile ===")

    name = input("Profile name [Android - Device Restrictions]: ").strip() or "Android - Device Restrictions"
    desc = input("Description (optional): ").strip() or "Android device restrictions"

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
        print(f"\n✅ Success! Android Configuration Profile created.")
        print(f"Name: {data.get('displayName')}")
        print(f"ID:   {data.get('id')}")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_android_profile()
    except Exception as e:
        print(f"Critical error: {e}")
