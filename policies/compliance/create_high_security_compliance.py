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

def create_high_security_compliance():
    """
    Creates a High Security Windows Compliance Policy in Intune.
    Assign this to privileged users: admins, finance, executives, sensitive roles.

    Stricter than Standard:
    - Windows 11 24H2 minimum OS
    - Machine risk score <= Low (instead of Medium)
    - Longer passwords (12 chars)
    - Shorter inactivity timeout (5 min)
    - Shorter password expiration (60 days)
    - BitLocker, Secure Boot, Code Integrity all required
    """
    print("\n=== Create High Security Compliance Policy ===")
    print("Assign this to admins, finance, executives, or any privileged group.\n")

    name = input("Policy name [Windows - High Security Compliance]: ").strip()
    if not name:
        name = "Windows - High Security Compliance"

    desc = input("Description [High security compliance for privileged users and sensitive devices]: ").strip()
    if not desc:
        desc = "High security compliance for privileged users and sensitive devices"

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    payload = {
        "@odata.type": "#microsoft.graph.windows10CompliancePolicy",
        "displayName": name,
        "description": desc,

        # --- Device Health (same as Standard — all required) ---
        "bitLockerEnabled":     True,
        "secureBootEnabled":    True,
        "codeIntegrityEnabled": True,

        # --- Device Properties (stricter — Windows 11 24H2 only) ---
        "osMinimumVersion": "10.0.26100",   # Windows 11 24H2
        "osMaximumVersion": None,

        # --- System Security: Password (stricter) ---
        "passwordRequired":                              True,
        "passwordBlockSimple":                           True,
        "passwordRequiredType":                          "alphanumeric",
        "passwordMinimumLength":                         12,    # 12 vs 8 in Standard
        "passwordExpirationDays":                        60,    # 60 vs 90 in Standard
        "passwordPreviousPasswordBlockCount":            10,
        "passwordMinutesOfInactivityBeforeLock":         5,     # 5 vs 15 in Standard

        # --- System Security: Network & Endpoint ---
        "firewallEnabled":     True,
        "antivirusRequired":   True,
        "antiSpywareRequired": True,
        "defenderEnabled":     True,

        # --- Microsoft Defender for Endpoint (stricter) ---
        # Low = only clean devices allowed (no active threats tolerated)
        "deviceThreatProtectionRequiredSecurityLevel": "low",  # Low vs Medium in Standard

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
        print(f"\n✅ Success! High Security Compliance Policy created.")
        print(f"Name: {data.get('displayName')}")
        print(f"ID:   {data.get('id')}")
        print(f"\nNext step: assign this policy using assign_policy.py")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_high_security_compliance()
    except Exception as e:
        print(f"Critical error: {e}")
