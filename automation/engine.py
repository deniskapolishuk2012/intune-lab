import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token
from core.logger import get_logger

log = get_logger("engine")

# =============================================================================
# BUNDLES
# =============================================================================

BUNDLES = {
    "security_baseline": {
        "description": "Core security — assigned to all Windows devices",
        "compliance": [
            "ed5e8291-f508-4553-a016-7b3bacf65b1a",  # Standard Compliance Policy
        ],
        "configuration": [
            "efeccb22-52d6-4281-ab35-3c11f6e2ba9d",  # Windows - Defender Antivirus
            "746458e1-1e4f-4453-9971-fd8ee97ef71a",  # Windows Firewall
            "d70ba5ba-33b4-49a8-b0dc-3d4fc6dcc42e",  # Attack Surface Reduction Rules
        ],
        "legacy": [
            "3bd1b2a7-1843-413d-912c-cc9411a7faeb",  # Windows - Update Ring Standard
        ],
        "apps": []
    },
    "standard_user": {
        "description": "Standard users — basic apps",
        "compliance":  [],
        "configuration": [
            "1640ac21-3462-4946-9d6c-e8049b76cc2a",  # Windows - Device Restrictions
            "2b5500a9-0b0b-4c90-bec4-27cd42bf33d6",  # Microsoft Edge Security
        ],
        "legacy": [],
        "apps": [
            "b1545685-cb41-4ce0-ab56-44ef861078d0",  # 7-Zip 24.07
        ]
    },
    "high_security": {
        "description": "IT/Admin — strict policies",
        "compliance": [
            "95910d10-0079-44c9-9b35-ee748854331e",  # High Security Compliance Policy
        ],
        "configuration": [
            "0916764c-c18e-40b1-b222-2cc9a04d8c57",  # BitLocker Disk Encryption
            "2b5500a9-0b0b-4c90-bec4-27cd42bf33d6",  # Microsoft Edge Security
        ],
        "legacy": [],
        "apps": [
            "b1545685-cb41-4ce0-ab56-44ef861078d0",  # 7-Zip 24.07
        ]
    },
    "restricted": {
        "description": "Non-compliant — restrict access",
        "compliance": [
            "ed5e8291-f508-4553-a016-7b3bacf65b1a",  # Standard Compliance Policy
        ],
        "configuration": [],
        "legacy": [],
        "apps": []
    },
}

# =============================================================================
# RULES ENGINE
# =============================================================================

def evaluate_rules(user: dict, device: dict) -> list:
    bundles = []

    if device.get("os", "Windows") == "Windows":
        bundles.append("security_baseline")
        log.debug(f"Rule 1: Windows device → security_baseline")

    compliance = device.get("complianceState", "").lower()
    if compliance and compliance not in ("compliant",):
        bundles.append("restricted")
        log.warning(f"Rule 2: Device is '{compliance}' → restricted bundle (overrides role)")
        return bundles

    job_title  = (user.get("jobTitle") or "").lower()
    department = (user.get("department") or "").lower()
    it_keywords = {"it", "admin", "administrator", "engineer", "devops", "security", "cloud"}
    is_it = (
        any(kw in job_title  for kw in it_keywords) or
        any(kw in department for kw in it_keywords)
    )

    if is_it:
        log.info(f"Rule 3: IT role detected (jobTitle='{user.get('jobTitle')}') → high_security")
        bundles.append("high_security")
    else:
        log.info(f"Rule 4: Standard user → standard_user bundle")
        bundles.append("standard_user")

    return bundles

# =============================================================================
# ACTIONS
# =============================================================================

def get_assigned_groups(token: str, url: str) -> set:
    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return set()
    return {a.get("target", {}).get("groupId") for a in response.json().get("value", [])}

def assign_compliance_policy(token: str, policy_id: str, group_id: str) -> str:
    check_url = f"https://graph.microsoft.com/v1.0/deviceManagement/deviceCompliancePolicies/{policy_id}/assignments"
    if group_id in get_assigned_groups(token, check_url):
        log.debug(f"Compliance {policy_id[:8]} → already assigned")
        return "⏭️  already assigned"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"assignments": [{"target": {"@odata.type": "#microsoft.graph.groupAssignmentTarget", "groupId": group_id}}]}
    resp    = requests.post(f"https://graph.microsoft.com/v1.0/deviceManagement/deviceCompliancePolicies/{policy_id}/assign", json=payload, headers=headers)
    if resp.status_code in (200, 201, 204):
        log.info(f"Compliance {policy_id[:8]} → ✅ assigned")
        return "✅ assigned"
    log.error(f"Compliance {policy_id[:8]} → ❌ failed ({resp.status_code})")
    return f"❌ failed ({resp.status_code})"

def assign_configuration_policy(token: str, policy_id: str, group_id: str) -> str:
    base_url  = f"https://graph.microsoft.com/beta/deviceManagement/configurationPolicies/{policy_id}"
    if group_id in get_assigned_groups(token, f"{base_url}/assignments"):
        log.debug(f"Configuration {policy_id[:8]} → already assigned")
        return "⏭️  already assigned"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"assignments": [{"target": {"@odata.type": "#microsoft.graph.groupAssignmentTarget", "groupId": group_id}}]}
    resp    = requests.post(f"{base_url}/assign", json=payload, headers=headers)
    if resp.status_code in (200, 201, 204):
        log.info(f"Configuration {policy_id[:8]} → ✅ assigned")
        return "✅ assigned"
    msg = resp.json().get('error', {}).get('message', '')[:80]
    log.error(f"Configuration {policy_id[:8]} → ❌ failed ({resp.status_code}): {msg}")
    return f"❌ failed ({resp.status_code})"

def assign_legacy_policy(token: str, policy_id: str, group_id: str) -> str:
    base_url  = f"https://graph.microsoft.com/v1.0/deviceManagement/deviceConfigurations/{policy_id}"
    if group_id in get_assigned_groups(token, f"{base_url}/assignments"):
        log.debug(f"Legacy {policy_id[:8]} → already assigned")
        return "⏭️  already assigned"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"assignments": [{"target": {"@odata.type": "#microsoft.graph.groupAssignmentTarget", "groupId": group_id}}]}
    resp    = requests.post(f"{base_url}/assign", json=payload, headers=headers)
    if resp.status_code in (200, 201, 204):
        log.info(f"Legacy {policy_id[:8]} → ✅ assigned")
        return "✅ assigned"
    log.error(f"Legacy {policy_id[:8]} → ❌ failed ({resp.status_code})")
    return f"❌ failed ({resp.status_code})"

def assign_app(token: str, app_id: str, group_id: str) -> str:
    check_url = f"https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/{app_id}/assignments"
    if group_id in get_assigned_groups(token, check_url):
        log.debug(f"App {app_id[:8]} → already assigned")
        return "⏭️  already assigned"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "intent": "required",
        "target": {"@odata.type": "#microsoft.graph.groupAssignmentTarget", "groupId": group_id},
        "settings": {
            "@odata.type":                 "#microsoft.graph.win32LobAppAssignmentSettings",
            "notifications":                "showAll",
            "restartSettings":              None,
            "installTimeSettings":          None,
            "deliveryOptimizationPriority": "notConfigured"
        }
    }
    resp = requests.post(check_url, json=payload, headers=headers)
    if resp.status_code in (200, 201):
        log.info(f"App {app_id[:8]} → ✅ assigned")
        return "✅ assigned"
    log.error(f"App {app_id[:8]} → ❌ failed ({resp.status_code})")
    return f"❌ failed ({resp.status_code})"

def apply_bundle(token: str, bundle_name: str, group_id: str, group_name: str):
    bundle = BUNDLES.get(bundle_name, {})
    log.info(f"Applying bundle: {bundle_name} → group: {group_name}")
    print(f"\n  Bundle: {bundle_name} — {bundle.get('description')}")

    for pid in bundle.get("compliance", []):
        status = assign_compliance_policy(token, pid, group_id)
        print(f"    [compliance]     {pid[:8]}...  {status}")

    for pid in bundle.get("configuration", []):
        status = assign_configuration_policy(token, pid, group_id)
        print(f"    [configuration]  {pid[:8]}...  {status}")

    for pid in bundle.get("legacy", []):
        status = assign_legacy_policy(token, pid, group_id)
        print(f"    [legacy]         {pid[:8]}...  {status}")

    for aid in bundle.get("apps", []):
        status = assign_app(token, aid, group_id)
        print(f"    [app]            {aid[:8]}...  {status}")

# =============================================================================
# CONTEXT
# =============================================================================

def get_user_context(token: str, upn: str) -> dict:
    url      = f"https://graph.microsoft.com/v1.0/users/{upn}?$select=displayName,jobTitle,department,userPrincipalName"
    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else {}

def get_device_context(token: str, device_name: str) -> dict:
    url = (
        f"https://graph.microsoft.com/v1.0/deviceManagement/managedDevices"
        f"?$filter=deviceName eq '{device_name}'"
        f"&$select=deviceName,operatingSystem,complianceState,userPrincipalName"
    )
    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        devices = response.json().get("value", [])
        if devices:
            d = devices[0]
            return {
                "name":            d.get("deviceName"),
                "os":              d.get("operatingSystem", "Windows"),
                "complianceState": d.get("complianceState", ""),
                "ownerUpn":        d.get("userPrincipalName"),
            }
    return {"os": "Windows", "complianceState": ""}

def get_groups(token: str) -> list:
    url      = "https://graph.microsoft.com/v1.0/groups?$filter=securityEnabled eq true&$select=id,displayName"
    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json().get("value", []) if response.status_code == 200 else []

# =============================================================================
# MAIN
# =============================================================================

def run_engine():
    print("\n" + "="*60)
    print("   INTUNE ASSIGNMENT AUTOMATION ENGINE")
    print("="*60)

    log.info("Engine started")

    token = get_access_token()
    if not token:
        log.error("Failed to obtain access token")
        return

    print("\n[1/4] Collect Context")
    print("  Mode:")
    print("    1. By user UPN + device name")
    print("    2. By device name only")
    print("    3. Manual input")
    mode = input("  Choose [1]: ").strip() or "1"

    user   = {}
    device = {"os": "Windows", "complianceState": ""}

    if mode == "1":
        upn  = input("  User UPN: ").strip()
        user = get_user_context(token, upn)
        log.info(f"User context: {upn} | jobTitle={user.get('jobTitle')} | dept={user.get('department')}")
        print(f"  User:       {user.get('displayName', 'N/A')}")
        print(f"  Job Title:  {user.get('jobTitle', 'N/A')}")
        print(f"  Department: {user.get('department', 'N/A')}")
        dev = input("  Device name (Enter to skip): ").strip()
        if dev:
            device = get_device_context(token, dev)
            log.info(f"Device context: {dev} | os={device.get('os')} | compliance={device.get('complianceState')}")
            print(f"  Device:     {device.get('name', 'N/A')}")
            print(f"  OS:         {device.get('os', 'N/A')}")
            print(f"  Compliance: {device.get('complianceState', 'N/A')}")

    elif mode == "2":
        dev    = input("  Device name: ").strip()
        device = get_device_context(token, dev)
        log.info(f"Device context: {dev} | compliance={device.get('complianceState')}")
        print(f"  Device:     {device.get('name', 'N/A')}")
        print(f"  Compliance: {device.get('complianceState', 'N/A')}")
        if device.get("ownerUpn"):
            user = get_user_context(token, device["ownerUpn"])
            log.info(f"Owner: {device['ownerUpn']} | jobTitle={user.get('jobTitle')}")

    else:
        user = {
            "jobTitle":   input("  Job Title: ").strip(),
            "department": input("  Department: ").strip(),
        }
        device = {
            "os":              input("  OS [Windows]: ").strip() or "Windows",
            "complianceState": input("  Compliance [compliant]: ").strip() or "compliant",
        }
        log.info(f"Manual context: jobTitle={user['jobTitle']} | compliance={device['complianceState']}")

    print("\n[2/4] Evaluate Rules")
    bundles = evaluate_rules(user, device)
    log.info(f"Bundles selected: {', '.join(bundles)}")
    print(f"  → Bundles: {', '.join(bundles)}")

    print("\n[3/4] Select Target Group")
    groups = get_groups(token)
    if not groups:
        log.error("No security groups found")
        return

    for i, g in enumerate(groups, start=1):
        print(f"  {i}. {g.get('displayName')}")

    choice = input("\n  Enter group number: ").strip()
    try:
        group = groups[int(choice) - 1]
    except (ValueError, IndexError):
        log.error("Invalid group selection")
        print("❌ Invalid choice.")
        return

    log.info(f"Target group: {group.get('displayName')} ({group.get('id')})")

    print(f"\n[4/4] Apply Bundles → '{group.get('displayName')}'")
    confirm = input(f"\n  Apply {len(bundles)} bundle(s)? [y/N]: ").strip().lower()
    if confirm != "y":
        log.info("Engine cancelled by user")
        print("Cancelled.")
        return

    for bundle_name in bundles:
        apply_bundle(token, bundle_name, group["id"], group["displayName"])

    log.info(f"Engine complete | group: {group.get('displayName')} | bundles: {', '.join(bundles)}")

    print("\n" + "="*60)
    print("  ✅ Engine complete.")
    print(f"  Group:   {group.get('displayName')}")
    print(f"  Bundles: {', '.join(bundles)}")
    print(f"  Log:     logs/engine_{__import__('datetime').datetime.now().strftime('%Y-%m-%d')}.log")
    print("="*60)

if __name__ == "__main__":
    try:
        run_engine()
    except Exception as e:
        import traceback
        log.critical(f"Critical error: {e}")
        traceback.print_exc()
