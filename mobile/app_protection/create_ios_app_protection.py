import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import requests
from core.auth import get_access_token

TEMPLATES = {
    "1": {
        "label": "Standard — protect corporate data in managed apps",
        "payload": {
            "@odata.type":                          "#microsoft.graph.iosManagedAppProtection",

            # --- Data Transfer ---
            "allowedInboundDataTransferSources":     "managedApps",   # Only from managed apps
            "allowedOutboundDataTransferDestinations": "managedApps", # Only to managed apps
            "allowedOutboundClipboardSharingLevel":  "managedAppsWithPasteIn",
            "saveAsBlocked":                          True,            # Block Save As
            "organizationalCredentialsRequired":      False,

            # --- Access requirements ---
            "pinRequired":                            True,
            "minimumPinLength":                       6,
            "pinCharacterSet":                        "numeric",
            "periodBeforePinReset":                   "P90D",          # Reset PIN every 90 days
            "allowedDataStorageLocations":            ["oneDriveForBusiness", "sharePoint"],
            "contactSyncBlocked":                     False,
            "printBlocked":                           True,            # Block printing

            # --- Conditional launch ---
            "maximumPinRetries":                      5,
            "simplePinBlocked":                       True,
            "fingerprintBlocked":                     False,           # Allow biometrics

            # --- Apps ---
            "apps": [
                {"id": "com.microsoft.outlook"},
                {"id": "com.microsoft.teams"},
                {"id": "com.microsoft.office"},
                {"id": "com.microsoft.sharepoint"},
                {"id": "com.microsoft.OneDrive"},
            ]
        }
    },
    "2": {
        "label": "Strict — block all external data transfer",
        "payload": {
            "@odata.type":                           "#microsoft.graph.iosManagedAppProtection",
            "allowedInboundDataTransferSources":      "none",          # No inbound transfer
            "allowedOutboundDataTransferDestinations": "none",         # No outbound transfer
            "allowedOutboundClipboardSharingLevel":   "blocked",       # Block clipboard
            "saveAsBlocked":                           True,
            "organizationalCredentialsRequired":       True,
            "pinRequired":                             True,
            "minimumPinLength":                        8,
            "pinCharacterSet":                         "alphanumericAndSymbol",
            "periodBeforePinReset":                    "P60D",
            "allowedDataStorageLocations":             ["oneDriveForBusiness"],
            "contactSyncBlocked":                      True,
            "printBlocked":                            True,
            "maximumPinRetries":                       3,
            "simplePinBlocked":                        True,
            "fingerprintBlocked":                      False,
            "apps": [
                {"id": "com.microsoft.outlook"},
                {"id": "com.microsoft.teams"},
                {"id": "com.microsoft.office"},
            ]
        }
    },
}

def create_ios_app_protection():
    """
    Creates an iOS App Protection Policy (MAM) in Intune via Microsoft Graph API.

    App Protection Policies work WITHOUT device enrollment (MAM-WE):
    - Protect corporate data inside managed apps (Outlook, Teams, Office)
    - Control copy/paste, save-as, data transfer between apps
    - Require PIN to access managed apps
    - Works on personal (BYOD) devices — no need to enroll

    This is the key difference from MDM:
    MDM = manage the device
    MAM = manage only the app and its data
    """
    print("\n=== Create iOS App Protection Policy (MAM) ===")
    print("ℹ️  App Protection works on personal devices without enrollment.\n")

    name = input("Policy name [iOS - App Protection Standard]: ").strip() or "iOS - App Protection Standard"
    desc = input("Description (optional): ").strip() or "iOS MAM policy for corporate apps"

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

    # Extract apps separately — they need to be added after policy creation
    apps = payload.pop("apps", [])

    url     = "https://graph.microsoft.com/beta/deviceAppManagement/iosManagedAppProtections"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\nCreating '{name}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data      = response.json()
        policy_id = data.get("id")
        print(f"\n✅ Success! iOS App Protection Policy created.")
        print(f"Name: {data.get('displayName')}")
        print(f"ID:   {policy_id}")

        # Add apps to policy
        if apps:
            print(f"\nAdding {len(apps)} protected app(s)...")
            apps_url = f"https://graph.microsoft.com/beta/deviceAppManagement/iosManagedAppProtections/{policy_id}/apps"
            for app in apps:
                app_payload = {
                    "id":          app["id"],
                    "mobileAppIdentifier": {
                        "@odata.type": "#microsoft.graph.iosMobileAppIdentifier",
                        "bundleId":    app["id"]
                    }
                }
                app_resp = requests.post(apps_url, json=app_payload, headers=headers)
                status = "✅" if app_resp.status_code in (200, 201) else f"❌ ({app_resp.status_code})"
                print(f"  {status} {app['id']}")

        print(f"\nTip: Assign this policy to user groups via Intune portal or assign_policy.py.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_ios_app_protection()
    except Exception as e:
        print(f"Critical error: {e}")
