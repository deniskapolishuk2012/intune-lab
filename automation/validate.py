import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

# =============================================================================
# VALIDATION — проверяет что политики и приложения реально назначены на группу
# "Я не верю что применилось — я проверяю"
# =============================================================================

def get_groups(token: str) -> list:
    url     = "https://graph.microsoft.com/v1.0/groups?$filter=securityEnabled eq true&$select=id,displayName"
    headers = {"Authorization": f"Bearer {token}"}
    resp    = requests.get(url, headers=headers)
    return resp.json().get("value", []) if resp.status_code == 200 else []

def check_compliance_assigned(token: str, policy_id: str, policy_name: str, group_id: str) -> tuple:
    """Returns (status_emoji, message)"""
    url     = f"https://graph.microsoft.com/v1.0/deviceManagement/deviceCompliancePolicies/{policy_id}/assignments"
    headers = {"Authorization": f"Bearer {token}"}
    resp    = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return "❌", f"{policy_name} — could not fetch assignments"
    assigned_groups = {a.get("target", {}).get("groupId") for a in resp.json().get("value", [])}
    if group_id in assigned_groups:
        return "✅", f"{policy_name} — assigned"
    return "⚠️ ", f"{policy_name} — NOT assigned"

def check_configuration_assigned(token: str, policy_id: str, policy_name: str, group_id: str) -> tuple:
    """Returns (status_emoji, message) for Settings Catalog policies"""
    url     = f"https://graph.microsoft.com/beta/deviceManagement/configurationPolicies/{policy_id}/assignments"
    headers = {"Authorization": f"Bearer {token}"}
    resp    = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return "❌", f"{policy_name} — could not fetch assignments"
    assigned_groups = {a.get("target", {}).get("groupId") for a in resp.json().get("value", [])}
    if group_id in assigned_groups:
        return "✅", f"{policy_name} — assigned"
    return "⚠️ ", f"{policy_name} — NOT assigned"

def check_legacy_assigned(token: str, policy_id: str, policy_name: str, group_id: str) -> tuple:
    """Returns (status_emoji, message) for legacy deviceConfigurations"""
    url     = f"https://graph.microsoft.com/v1.0/deviceManagement/deviceConfigurations/{policy_id}/assignments"
    headers = {"Authorization": f"Bearer {token}"}
    resp    = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return "❌", f"{policy_name} — could not fetch assignments"
    assigned_groups = {a.get("target", {}).get("groupId") for a in resp.json().get("value", [])}
    if group_id in assigned_groups:
        return "✅", f"{policy_name} — assigned"
    return "⚠️ ", f"{policy_name} — NOT assigned"

def check_app_assigned(token: str, app_id: str, app_name: str, group_id: str) -> tuple:
    """Returns (status_emoji, message) for Win32 apps"""
    url     = f"https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/{app_id}/assignments"
    headers = {"Authorization": f"Bearer {token}"}
    resp    = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return "❌", f"{app_name} — could not fetch assignments"
    assigned_groups = {a.get("target", {}).get("groupId") for a in resp.json().get("value", [])}
    if group_id in assigned_groups:
        return "✅", f"{app_name} — assigned"
    return "⚠️ ", f"{app_name} — NOT assigned"

def check_device_compliance(token: str, device_name: str) -> tuple:
    """Checks real compliance state of a device in Intune"""
    url = (
        f"https://graph.microsoft.com/v1.0/deviceManagement/managedDevices"
        f"?$filter=deviceName eq '{device_name}'"
        f"&$select=deviceName,complianceState,lastSyncDateTime,isEncrypted"
    )
    headers = {"Authorization": f"Bearer {token}"}
    resp    = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return "❌", f"Could not fetch device '{device_name}'"
    devices = resp.json().get("value", [])
    if not devices:
        return "⚠️ ", f"Device '{device_name}' not found in Intune"
    d = devices[0]
    state     = d.get("complianceState", "unknown")
    encrypted = d.get("isEncrypted", False)
    last_sync = d.get("lastSyncDateTime", "N/A")
    emoji = "✅" if state == "compliant" else "⚠️ "
    return emoji, f"{device_name} — compliance: {state} | encrypted: {encrypted} | last sync: {last_sync}"

# =============================================================================
# VALIDATION PROFILES — what to check per scenario
# =============================================================================

CHECKS = {
    "security_baseline": {
        "label": "Security Baseline",
        "compliance": [
            ("ed5e8291-f508-4553-a016-7b3bacf65b1a", "Standard Compliance Policy"),
        ],
        "configuration": [
            ("efeccb22-52d6-4281-ab35-3c11f6e2ba9d", "Windows - Defender Antivirus"),
            ("746458e1-1e4f-4453-9971-fd8ee97ef71a", "Windows Firewall"),
            ("d70ba5ba-33b4-49a8-b0dc-3d4fc6dcc42e", "ASR Rules"),
        ],
        "legacy": [
            ("3bd1b2a7-1843-413d-912c-cc9411a7faeb", "Update Ring Standard"),
        ],
        "apps": []
    },
    "standard_user": {
        "label": "Standard User Bundle",
        "compliance": [],
        "configuration": [
            ("1640ac21-3462-4946-9d6c-e8049b76cc2a", "Device Restrictions"),
            ("2b5500a9-0b0b-4c90-bec4-27cd42bf33d6", "Edge Security"),
        ],
        "legacy": [],
        "apps": [
            ("b1545685-cb41-4ce0-ab56-44ef861078d0", "7-Zip 24.07"),
        ]
    },
    "high_security": {
        "label": "High Security Bundle",
        "compliance": [
            ("95910d10-0079-44c9-9b35-ee748854331e", "High Security Compliance Policy"),
        ],
        "configuration": [
            ("0916764c-c18e-40b1-b222-2cc9a04d8c57", "BitLocker Disk Encryption"),
            ("2b5500a9-0b0b-4c90-bec4-27cd42bf33d6", "Edge Security"),
        ],
        "legacy": [],
        "apps": [
            ("b1545685-cb41-4ce0-ab56-44ef861078d0", "7-Zip 24.07"),
        ]
    },
}

def run_validation():
    """
    Validates that policies and apps are correctly assigned to a group.
    Optionally also checks real device compliance state.
    """
    print("\n" + "="*60)
    print("   INTUNE ASSIGNMENT VALIDATION")
    print("="*60)

    token = get_access_token()
    if not token:
        print("❌ Could not obtain token.")
        return

    # Pick group
    print("\nFetching groups...")
    groups = get_groups(token)
    if not groups:
        print("❌ No groups found.")
        return

    print("\nSelect group to validate:")
    for i, g in enumerate(groups, start=1):
        print(f"  {i}. {g.get('displayName')}")

    choice = input("\nEnter group number: ").strip()
    try:
        group = groups[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ Invalid choice.")
        return

    group_id   = group["id"]
    group_name = group["displayName"]

    # Pick bundles to validate
    print(f"\nWhat to validate for '{group_name}':")
    print("  1. Security Baseline")
    print("  2. Standard User Bundle")
    print("  3. High Security Bundle")
    print("  4. All bundles")

    choice2  = input("\nEnter number [4]: ").strip() or "4"
    if choice2 == "1":
        bundle_keys = ["security_baseline"]
    elif choice2 == "2":
        bundle_keys = ["standard_user"]
    elif choice2 == "3":
        bundle_keys = ["high_security"]
    else:
        bundle_keys = list(CHECKS.keys())

    # Run checks
    total = 0
    passed = 0

    for key in bundle_keys:
        check = CHECKS[key]
        print(f"\n--- {check['label']} ---")

        for pid, name in check.get("compliance", []):
            emoji, msg = check_compliance_assigned(token, pid, name, group_id)
            print(f"  {emoji} [compliance]     {msg}")
            total += 1
            if emoji == "✅":
                passed += 1

        for pid, name in check.get("configuration", []):
            emoji, msg = check_configuration_assigned(token, pid, name, group_id)
            print(f"  {emoji} [configuration]  {msg}")
            total += 1
            if emoji == "✅":
                passed += 1

        for pid, name in check.get("legacy", []):
            emoji, msg = check_legacy_assigned(token, pid, name, group_id)
            print(f"  {emoji} [legacy]         {msg}")
            total += 1
            if emoji == "✅":
                passed += 1

        for aid, name in check.get("apps", []):
            emoji, msg = check_app_assigned(token, aid, name, group_id)
            print(f"  {emoji} [app]            {msg}")
            total += 1
            if emoji == "✅":
                passed += 1

    # Optional device check
    device_name = input("\nCheck device compliance state? Enter device name (or Enter to skip): ").strip()
    if device_name:
        print(f"\n--- Device State ---")
        emoji, msg = check_device_compliance(token, device_name)
        print(f"  {emoji} {msg}")

    # Summary
    print("\n" + "="*60)
    print(f"  RESULT: {passed}/{total} checks passed")
    if passed == total:
        print("  ✅ All assignments verified successfully.")
    else:
        print(f"  ⚠️  {total - passed} assignment(s) missing — run engine.py to fix.")
    print("="*60)

if __name__ == "__main__":
    try:
        run_validation()
    except Exception as e:
        import traceback
        print(f"Critical error: {e}")
        traceback.print_exc()
