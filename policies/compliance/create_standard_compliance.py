import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import requests
from core.auth import get_access_token

# Required by Graph API — every compliance policy must have at least one scheduled action.
SCHEDULED_ACTIONS = [
    {
        "ruleName": "PasswordRequired",
        "scheduledActionConfigurations": [
            {
                "actionType":               "block",
                "gracePeriodHours":         0,
                "notificationTemplateId":   "",
                "notificationMessageCCList": []
            }
        ]
    }
]

def create_standard_compliance():
    """
    Creates the Standard (main) Windows Compliance Policy in Intune.
    Assign this to the majority of devices in your tenant.

    Covers:
    - Device Health: BitLocker, Secure Boot, Code Integrity
    - Device Properties: Minimum OS version (Win10 22H2)
    - System Security: Password, Firewall, Antivirus, Antispyware
    - Defender for Endpoint: Machine risk score <= Medium
    """
    print("\n=== Create Standard Compliance Policy ===")
    print("This is the main policy — assign it to most devices.\n")

    name = input("Policy name [Windows - Standard Compliance]: ").strip()
    if not name:
        name = "Windows - Standard Compliance"

    desc = input("Description [Standard compliance policy for all managed Windows devices]: ").strip()
    if not desc:
        desc = "Standard compliance policy for all managed Windows devices"

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    payload = {
        "@odata.type": "#microsoft.graph.windows10CompliancePolicy",
        "displayName": name,
        "description": desc,

        # --- Device Health ---
        "bitLockerEnabled":     True,   # Require BitLocker
        "secureBootEnabled":    True,   # Require Secure Boot
        "codeIntegrityEnabled": True,   # Require Code Integrity (HVCI)
        # Note: TPM is enforced implicitly when BitLocker + Secure Boot are required

        # --- Device Properties ---
        "osMinimumVersion": "10.0.19045",   # Windows 10 22H2 minimum
        "osMaximumVersion": None,            # Not configured — no upper limit

        # --- System Security: Password ---
        "passwordRequired":                              True,
        "passwordBlockSimple":                           True,   # Block simple passwords
        "passwordRequiredType":                          "alphanumeric",
        "passwordMinimumLength":                         8,
        "passwordExpirationDays":                        90,
        "passwordPreviousPasswordBlockCount":            10,
        "passwordMinutesOfInactivityBeforeLock":         15,

        # --- System Security: Network & Endpoint ---
        "firewallEnabled":    True,   # Require Microsoft Defender Firewall
        "antivirusRequired":  True,   # Require antivirus
        "antiSpywareRequired": True,  # Require antispyware
        "defenderEnabled":    True,   # Require Microsoft Defender

        # --- Microsoft Defender for Endpoint ---
        # Allowed machine risk scores: none, low, medium, high, notSet
        "deviceThreatProtectionRequiredSecurityLevel": "medium",  # <= Medium risk score

        # --- Scheduled Action (required by Graph API) ---
        "scheduledActionsForRule": SCHEDULED_ACTIONS
    }

    url     = "https://graph.microsoft.com/v1.0/deviceManagement/deviceCompliancePolicies"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    print(f"\nCreating '{name}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! Standard Compliance Policy created.")
        print(f"Name: {data.get('displayName')}")
        print(f"ID:   {data.get('id')}")
        print(f"\nNext step: assign this policy using assign_policy.py")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_standard_compliance()
    except Exception as e:
        print(f"Critical error: {e}")
