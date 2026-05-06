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
        "label": "Standard iOS — password + encryption + OS version",
        "payload": {
            "@odata.type":                     "#microsoft.graph.iosCompliancePolicy",
            "passcodeRequired":                 True,
            "passcodeMinimumLength":            6,
            "passcodeRequiredType":             "numeric",
            "passcodeBlockSimple":              True,
            "passcodeExpirationDays":           90,
            "passcodePreviousPasscodeBlockCount": 5,
            "passcodeMinutesOfInactivityBeforeLock": 5,
            "securityBlockJailbrokenDevices":   True,   # Block jailbroken devices
            "deviceThreatProtectionEnabled":    False,
            "osMinimumVersion":                 "16.0",
            "osMaximumVersion":                 None,
            "managedEmailProfileRequired":      False,
        }
    },
    "2": {
        "label": "Strict iOS — longer password + Defender risk score",
        "payload": {
            "@odata.type":                       "#microsoft.graph.iosCompliancePolicy",
            "passcodeRequired":                   True,
            "passcodeMinimumLength":              8,
            "passcodeRequiredType":               "alphanumeric",
            "passcodeBlockSimple":                True,
            "passcodeExpirationDays":             60,
            "passcodePreviousPasscodeBlockCount": 10,
            "passcodeMinutesOfInactivityBeforeLock": 2,
            "securityBlockJailbrokenDevices":     True,
            "deviceThreatProtectionEnabled":      True,
            "deviceThreatProtectionRequiredSecurityLevel": "low",
            "osMinimumVersion":                   "17.0",
            "osMaximumVersion":                   None,
            "managedEmailProfileRequired":        False,
        }
    },
}

def create_ios_compliance():
    """
    Creates an iOS/iPadOS compliance policy in Intune via Microsoft Graph API.

    Covers:
    - Passcode requirements (length, type, expiry)
    - Block jailbroken devices
    - Minimum OS version
    - Optional: Defender for Endpoint risk score
    """
    print("\n=== Create iOS Compliance Policy ===")

    name = input("Policy name [iOS - Standard Compliance]: ").strip() or "iOS - Standard Compliance"
    desc = input("Description (optional): ").strip() or "iOS compliance policy"

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
    payload["displayName"]          = name
    payload["description"]          = desc
    payload["scheduledActionsForRule"] = SCHEDULED_ACTIONS

    url     = "https://graph.microsoft.com/v1.0/deviceManagement/deviceCompliancePolicies"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\nCreating '{name}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! iOS Compliance Policy created.")
        print(f"Name: {data.get('displayName')}")
        print(f"ID:   {data.get('id')}")
        print(f"\nTip: Use assign_policy.py to assign to an iOS device group.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_ios_compliance()
    except Exception as e:
        print(f"Critical error: {e}")
