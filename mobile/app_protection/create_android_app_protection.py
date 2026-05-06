import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import requests
from core.auth import get_access_token

TEMPLATES = {
    "1": {
        "label": "Standard — protect corporate data in managed apps",
        "payload": {
            "@odata.type":                           "#microsoft.graph.androidManagedAppProtection",

            # --- Data Transfer ---
            "allowedInboundDataTransferSources":      "managedApps",
            "allowedOutboundDataTransferDestinations": "managedApps",
            "allowedOutboundClipboardSharingLevel":   "managedAppsWithPasteIn",
            "saveAsBlocked":                           True,

            # --- Access requirements ---
            "pinRequired":                             True,
            "minimumPinLength":                        6,
            "pinCharacterSet":                         "numeric",
            "periodBeforePinReset":                    "P90D",
            "allowedDataStorageLocations":             ["oneDriveForBusiness", "sharePoint"],
            "contactSyncBlocked":                      False,
            "printBlocked":                            True,
            "maximumPinRetries":                       5,
            "simplePinBlocked":                        True,
            "fingerprintAndBiometricEnabled":          True,   # Allow biometrics

            # --- Android specific ---
            "screenCaptureBlocked":                    True,   # Block screenshots
            "disableAppEncryptionIfDeviceEncryptionIsEnabled": False,
            "encryptAppData":                          True,   # Encrypt app data

            # --- Apps ---
            "apps": [
                {"id": "com.microsoft.outlook"},
                {"id": "com.microsoft.teams"},
                {"id": "com.microsoft.office"},
                {"id": "com.microsoft.sharepoint"},
                {"id": "com.microsoft.skydrive"},
            ]
        }
    },
    "2": {
        "label": "Strict — block all external data transfer",
        "payload": {
            "@odata.type":                            "#microsoft.graph.androidManagedAppProtection",
            "allowedInboundDataTransferSources":       "none",
            "allowedOutboundDataTransferDestinations": "none",
            "allowedOutboundClipboardSharingLevel":    "blocked",
            "saveAsBlocked":                            True,
            "pinRequired":                              True,
            "minimumPinLength":                         8,
            "pinCharacterSet":                          "alphanumericAndSymbol",
            "periodBeforePinReset":                     "P60D",
            "allowedDataStorageLocations":              ["oneDriveForBusiness"],
            "contactSyncBlocked":                       True,
            "printBlocked":                             True,
            "maximumPinRetries":                        3,
            "simplePinBlocked":                         True,
            "fingerprintAndBiometricEnabled":           False,
            "screenCaptureBlocked":                     True,
            "encryptAppData":                           True,
            "apps": [
                {"id": "com.microsoft.outlook"},
                {"id": "com.microsoft.teams"},
            ]
        }
    },
}

def create_android_app_protection():
    """
    Creates an Android App Protection Policy (MAM) in Intune via Microsoft Graph API.

    Works WITHOUT device enrollment — protects corporate data inside managed apps.
    Key Android-specific settings:
    - Encrypt app data at rest
    - Block screenshots within managed apps
    - Require PIN to open managed apps
    - Control clipboard between managed/unmanaged apps
    """
    print("\n=== Create Android App Protection Policy (MAM) ===")
    print("ℹ️  App Protection works on personal devices without enrollment.\n")

    name = input("Policy name [Android - App Protection Standard]: ").strip() or "Android - App Protection Standard"
    desc = input("Description (optional): ").strip() or "Android MAM policy for corporate apps"

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
    payload["description"] = desc

    apps = payload.pop("apps", [])

    url     = "https://graph.microsoft.com/beta/deviceAppManagement/androidManagedAppProtections"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\nCreating '{name}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data      = response.json()
        policy_id = data.get("id")
        print(f"\n✅ Success! Android App Protection Policy created.")
        print(f"Name: {data.get('displayName')}")
        print(f"ID:   {policy_id}")

        if apps:
            print(f"\nAdding {len(apps)} protected app(s)...")
            apps_url = f"https://graph.microsoft.com/beta/deviceAppManagement/androidManagedAppProtections/{policy_id}/apps"
            for app in apps:
                app_payload = {
                    "id": app["id"],
                    "mobileAppIdentifier": {
                        "@odata.type": "#microsoft.graph.androidMobileAppIdentifier",
                        "packageId":   app["id"]
                    }
                }
                app_resp = requests.post(apps_url, json=app_payload, headers=headers)
                status = "✅" if app_resp.status_code in (200, 201) else f"❌ ({app_resp.status_code})"
                print(f"  {status} {app['id']}")

        print(f"\nTip: Assign this policy to user groups via assign_policy.py.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_android_app_protection()
    except Exception as e:
        print(f"Critical error: {e}")