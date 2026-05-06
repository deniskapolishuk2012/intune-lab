# 🛡️ Intune Lab — Microsoft Intune Automation via Graph API

> A comprehensive Python-based automation toolkit for Microsoft Intune, built on top of the Microsoft Graph API. Covers the full MDM/MAM lifecycle: users, groups, devices, policies, apps, autopilot, mobile, conditional access, and an intelligent rule-based assignment engine.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Project Structure](#project-structure)
- [Modules](#modules)
- [Automation Engine](#automation-engine)
- [Conditional Access](#conditional-access)
- [Author](#author)

---

## Overview

This project automates Microsoft Intune management tasks that would otherwise require manual portal interaction. Everything is driven by Microsoft Graph API calls — no PowerShell, no portal clicks.

**Key capabilities:**
- Create and manage users, groups, licenses, and Temporary Access Passes (TAP)
- Deploy compliance policies and configuration profiles for Windows, iOS, and Android
- Upload and assign Win32 applications to device groups
- Configure Windows Autopilot deployment profiles
- Apply App Protection Policies (MAM) for iOS and Android — no enrollment required
- Conditional Access policies: MFA for admins, compliant device enforcement, legacy auth blocking
- Run an intelligent assignment engine based on user role and device compliance state
- Validate assignments with a dedicated validation script
- Full logging to daily rotating log files

---

## Architecture

```
          INPUT
     (user / device)
            ↓
         RULES
  (role / compliance / OS)
            ↓
        ENGINE
   (makes the decision)
            ↓
        ACTIONS
  (assign policy / app)
            ↓
       VALIDATE
  (verify it worked)
```

### Assignment Logic (Zero Trust)

```
Priority 1 → Security baseline    always assigned to all Windows devices
Priority 2 → Compliance state     non-compliant overrides role → restricted bundle
Priority 3 → Role detection       IT/Admin → high_security | everyone else → standard_user
Priority 4 → Default fallback     standard_user if nothing matched
```

---

## Prerequisites

- Python 3.10+
- Microsoft Intune tenant (trial works)
- Azure AD App Registration with the following **Application** permissions + Admin Consent:

| Permission | Used for |
|---|---|
| `DeviceManagementManagedDevices.ReadWrite.All` | Device management |
| `DeviceManagementManagedDevices.PrivilegedOperations.All` | Sync, wipe, retire |
| `DeviceManagementConfiguration.ReadWrite.All` | Configuration profiles |
| `DeviceManagementApps.ReadWrite.All` | App upload and assignment |
| `DeviceManagementServiceConfig.ReadWrite.All` | Autopilot profiles |
| `User.ReadWrite.All` | User management |
| `Group.ReadWrite.All` | Group management |
| `Organization.Read.All` | License SKU fetching |
| `Policy.ReadWrite.ConditionalAccess` | Conditional Access policies |
| `UserAuthenticationMethod.ReadWrite.All` | Temporary Access Pass (TAP) |

---

## Setup

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/intune-lab.git
cd intune-lab
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure credentials**
```bash
cp .env.example .env
```

Fill in `.env` with your App Registration values:
```
TENANT_ID=your-tenant-id
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
DOMAIN=your-domain.onmicrosoft.com
```

**4. Run any script**
```bash
python users/create_user.py
python automation/engine.py
```

---

## Project Structure

```
intune_lab/
├── .env.example
├── .gitignore
├── requirements.txt
├── core/
│   ├── auth.py                              # Token acquisition via MSAL + .env
│   └── logger.py                            # Daily rotating log files
├── users/
│   ├── create_user.py
│   ├── create_group.py
│   ├── create_device_group.py
│   ├── create_dynamic_user_group.py         # Requires Entra P1
│   ├── create_dynamic_device_group.py       # Requires Entra P1
│   ├── assign_license.py
│   ├── create_tap.py                        # Temporary Access Pass
│   ├── list_tap.py
│   └── delete_tap.py
├── devices/
│   ├── list_devices.py
│   ├── device_details.py
│   ├── device_sync.py
│   ├── retire_device.py
│   └── wipe_device.py
├── policies/
│   ├── compliance/
│   │   ├── create_standard_compliance.py
│   │   └── create_high_security_compliance.py
│   ├── configuration/
│   │   ├── create_defender_antivirus.py
│   │   ├── create_firewall.py
│   │   ├── create_asr_rules.py
│   │   ├── create_bitlocker.py
│   │   ├── create_update_ring.py
│   │   ├── create_device_restrictions.py
│   │   └── create_edge_security.py
│   ├── assign_policy.py
│   └── list_policies.py
├── apps/
│   ├── upload_win32_app.py
│   ├── assign_app.py
│   └── list_apps.py
├── autopilot/
│   ├── upload_autopilot_device.py
│   ├── list_autopilot_devices.py
│   ├── create_deployment_profile.py
│   └── assign_deployment_profile.py
├── mobile/
│   ├── compliance/
│   │   ├── create_ios_compliance.py
│   │   └── create_android_compliance.py
│   ├── configuration/
│   │   ├── create_ios_profile.py
│   │   └── create_android_profile.py
│   └── app_protection/
│       ├── create_ios_app_protection.py
│       └── create_android_app_protection.py
├── conditional_access/
│   ├── create_require_mfa_admins.py
│   ├── create_require_compliant_device.py
│   ├── create_block_legacy_auth.py
│   ├── create_named_location.py
│   ├── list_ca_policies.py
│   └── enable_ca_policy.py
├── reporting/
│   ├── non_compliant_devices.py
│   ├── inactive_devices.py
│   ├── devices_without_bitlocker.py
│   └── licensed_users_report.py
├── automation/
│   ├── engine.py
│   └── validate.py
└── logs/
    └── engine_YYYY-MM-DD.log
```

---

## Modules

### 👥 Users

| Script | Description |
|---|---|
| `create_user.py` | Create Azure AD user interactively |
| `create_group.py` | Security group with optional members |
| `create_device_group.py` | Device group — add computers by name |
| `create_dynamic_user_group.py` | Dynamic group by jobTitle, department, license |
| `create_dynamic_device_group.py` | Dynamic device group by OS, name prefix, Autopilot profile |
| `assign_license.py` | Assign Intune/M365 license — auto-fetches available SKUs |
| `create_tap.py` | Create Temporary Access Pass for onboarding or MFA recovery |
| `list_tap.py` | List active TAPs for a user |
| `delete_tap.py` | Revoke a TAP |

### 💻 Devices

| Script | Description |
|---|---|
| `list_devices.py` | All Intune managed devices with compliance state |
| `device_details.py` | Owner, OS, compliance, last sync, BitLocker state |
| `device_sync.py` | Force immediate check-in with Intune |
| `retire_device.py` | Remove company data — personal data intact |
| `wipe_device.py` | ⚠️ Factory reset — double confirmation required |

### 📋 Policies — Windows

| Script | Description |
|---|---|
| `create_standard_compliance.py` | BitLocker + Defender + password + OS version (Win10 22H2+) |
| `create_high_security_compliance.py` | Win11 24H2 only, Low risk score, 12-char password, 5 min lock |
| `create_defender_antivirus.py` | Real-time, cloud High, PUA block, behavior monitoring |
| `create_firewall.py` | All profiles ON, block inbound by default |
| `create_asr_rules.py` | Block LSASS, Office child processes, email executables, obfuscated scripts |
| `create_bitlocker.py` | XTS-AES-128 + TPM + recovery key escrow to Azure AD |
| `create_update_ring.py` | Pilot / Standard / Broad rings with configurable deferral |
| `create_device_restrictions.py` | Block USB, camera, Bluetooth, screenshots, Store |
| `create_edge_security.py` | SmartScreen ON, block InPrivate, block popups, prevent bypass |

### 📱 Mobile

| Script | Description |
|---|---|
| `create_ios_compliance.py` | Passcode, jailbreak block, min OS version |
| `create_android_compliance.py` | Password, encryption, root block, USB debugging off |
| `create_ios_profile.py` | Block camera, screenshots, iCloud, AirDrop, iTunes |
| `create_android_profile.py` | Block camera, NFC, USB storage, clipboard sharing |
| `create_ios_app_protection.py` | MAM — protect Outlook/Teams/Office without device enrollment |
| `create_android_app_protection.py` | MAM + app data encryption + screenshot block |

> **MDM vs MAM:** MDM manages the entire device. MAM (App Protection) manages only the app and its data — works on personal BYOD devices without enrollment.

### 🚀 Autopilot

| Script | Description |
|---|---|
| `upload_autopilot_device.py` | Upload device via hardware hash CSV from `Get-WindowsAutopilotInfo` |
| `list_autopilot_devices.py` | List registered Autopilot devices with profile status |
| `create_deployment_profile.py` | OOBE profile — hide EULA, privacy screens, set user type |
| `assign_deployment_profile.py` | Assign deployment profile to Azure AD group |

### 📊 Reporting

| Script | Description |
|---|---|
| `non_compliant_devices.py` | All devices not in compliant state with owner and last sync |
| `inactive_devices.py` | Devices with no sync > N days — identify stale/orphaned devices |
| `devices_without_bitlocker.py` | Windows devices where `isEncrypted = false` |
| `licensed_users_report.py` | Licensed vs unlicensed users — with full pagination support |

---

## Automation Engine

The engine (`automation/engine.py`) implements a rule-based assignment system.

```bash
python automation/engine.py
```

**Input modes:**
- Mode 1: User UPN + optional device name — fetches real attributes from Azure AD / Intune
- Mode 2: Device name only — resolves owner automatically
- Mode 3: Manual input — for testing specific scenarios

**Bundles:**

| Bundle | Triggered when | Contains |
|---|---|---|
| `security_baseline` | Always (Windows) | Standard Compliance + Defender + Firewall + ASR + Update Ring |
| `standard_user` | Non-IT users | Device Restrictions + Edge Security + 7-Zip |
| `high_security` | IT/Admin role detected | High Security Compliance + BitLocker + Edge Security + 7-Zip |
| `restricted` | Device non-compliant | Standard Compliance only — blocks role rules |

**Idempotent** — safe to run multiple times. Already-assigned policies are skipped.

### Validation

```bash
python automation/validate.py
```

Verifies that expected assignments are present. Reports per-policy pass/fail.

### Logging

```
[2026-05-05 10:52:01] INFO     | engine | Engine started
[2026-05-05 10:52:03] INFO     | engine | User: denis@dpintune.onmicrosoft.com | jobTitle=Cloud Security Engineer
[2026-05-05 10:52:04] INFO     | engine | Bundles selected: security_baseline, high_security
[2026-05-05 10:52:06] INFO     | engine | Configuration efeccb22 → ✅ assigned
[2026-05-05 10:52:09] WARNING  | engine | Device is noncompliant → restricted bundle
```

---

## Conditional Access

> ⚠️ Requires Entra ID Premium P1/P2. All policies created in **Report-Only** mode by default.

| Script | Policy | Description |
|---|---|---|
| `create_require_mfa_admins.py` | CA001 | MFA required for all admin roles |
| `create_require_compliant_device.py` | CA002 | M365 access blocked from non-compliant devices |
| `create_block_legacy_auth.py` | CA003 | Block IMAP/POP3/SMTP — these bypass MFA completely |
| `create_named_location.py` | — | Define trusted countries for location-based policies |
| `list_ca_policies.py` | — | List all CA policies with current state |
| `enable_ca_policy.py` | — | Switch policy: report-only → enabled → disabled |

### Deployment order

```
1. create_named_location.py           ← define trusted locations first
2. create_block_legacy_auth.py        ← lowest risk, highest security gain
3. create_require_mfa_admins.py       ← protect privileged accounts
4. create_require_compliant_device.py ← enforce Intune compliance
```

### Report-Only → Enabled workflow

```bash
# 1. Create in report-only (default)
python conditional_access/create_require_mfa_admins.py

# 2. Monitor sign-in logs for 1-2 weeks in Entra portal

# 3. Enable when confident
python conditional_access/enable_ca_policy.py
```

---

## Temporary Access Pass (TAP)

TAP is a time-limited passcode for passwordless onboarding and MFA recovery.

**Use cases:**
- New employee → give TAP instead of temporary password → user registers authenticator on first sign-in
- User lost phone → give TAP to re-register MFA methods
- FIDO2 key bootstrap → TAP required for first-time passwordless setup

```bash
python users/create_tap.py      # Create TAP
python users/list_tap.py        # View active TAPs
python users/delete_tap.py      # Revoke TAP
```

---

## Author

**Denis** — Cloud Security Engineer
Specializing in Microsoft Security Stack
Certifications: AZ-500, AZ-104 | Preparing: SC-200

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com/in/yourprofile)

---

> Built as a hands-on Intune lab for SC-200 exam preparation and real-world cloud security practice.
