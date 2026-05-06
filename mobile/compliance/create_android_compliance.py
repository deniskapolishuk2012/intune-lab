import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import requests
from core.auth import get_access_token

SCHEDULED_ACTIONS = [
    {
        "ruleName": "PasswordRequired",
        "scheduledActionConfigurations": [
            {
                "actionType":                "block",
                "gracePeriodHours":          0,
                "notificationTemplateId":    "",
                "notificationMessageCCList": []
            }
        ]
    }
]

TEMPLATES = {
    "1": {
        "label": "Standard Android Enterprise — password + encryption",
        "payload": {
            "@odata.type":                          "#microsoft.graph.androidCompliancePolicy",
            "passwordRequired":                      True,
            "passwordMinimumLength":                 6,
            "passwordRequiredType":                  "numeric",
            "passwordExpirationDays":                90,
            "passwordPreviousPasswordBlockCount":    5,
            "passwordMinutesOfInactivityBeforeLock": 5,
            "storageRequireEncryption":              True,
            "securityBlockJailbrokenDevices":        True,   # Block rooted devices
            "securityDisableUsbDebugging":           True,
            "osMinimumVersion":                      "11.0",
            "osMaximumVersion":                      None,
        }
    },
    "2": {
        "label": "Strict Android — alphanumeric + Defender risk score",
        "payload": {
            "@odata.type":                           "#microsoft.graph.androidCompliancePolicy",
            "passwordRequired":                       True,
            "passwordMinimumLength":                  8,
            "passwordRequiredType":                   "alphanumericWithSymbols",
            "passwordExpirationDays":                 60,
            "passwordPreviousPasswordBlockCount":     10,
            "passwordMinutesOfInactivityBeforeLock":  2,
            "storageRequireEncryption":               True,
            "securityBlockJailbrokenDevices":         True,
            "securityDisableUsbDebugging":            True,
            "deviceThreatProtectionEnabled":          True,
            "deviceThreatProtectionRequiredSecurityLevel": "low",
            "osMinimumVersion":                       "13.0",
            "osMaximumVersion":                       None,
        }
    },
}

def create_android_compliance():
    """
    Creates an Android compliance policy in Intune via Microsoft Graph API.

    Covers:
    - Password requirements
    - Storage encryption
    - Block rooted devices
    - Disable USB debugging
    - Minimum OS version
    - Optional: Defender for Endpoint risk score
    """
    print("\n=== Create Android Compliance Policy ===")

    name = input("Policy name [Android - Standard Compliance]: ").strip() or "Android - Standard Compliance"
    desc = input("Description (optional): ").strip() or "Android compliance policy"

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
    payload["displayName"]             = name
    payload["description"]             = desc
    payload["scheduledActionsForRule"] = SCHEDULED_ACTIONS

    url     = "https://graph.microsoft.com/v1.0/deviceManagement/deviceCompliancePolicies"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\nCreating '{name}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! Android Compliance Policy created.")
        print(f"Name: {data.get('displayName')}")
        print(f"ID:   {data.get('id')}")
        print(f"\nTip: Use assign_policy.py to assign to an Android device group.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_android_compliance()
    except Exception as e:
        print(f"Critical error: {e}")
