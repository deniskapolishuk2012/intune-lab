import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import requests
from core.auth import get_access_token

def create_bitlocker():
    """
    Creates a BitLocker disk encryption profile via Settings Catalog API.

    Startup authentication children values (confirmed from API error responses):
    - configurenontpmstartupkeyusage: 0=Blocked, 1=Required
    - configuretpmusagedropdown:      0=Blocked, 1=Required, 2=Allowed
    - configurepinusagedropdown:      0=Blocked, 1=Required, 2=Allowed
    - configuretpmstartupkeyusagedropdown: 0=Blocked, 1=Required, 2=Allowed
    - configuretpmpinkeyusagedropdown:     0=Blocked, 1=Required, 2=Allowed
    """
    print("\n=== Create Profile: BitLocker Disk Encryption ===")

    name = input("Profile name [Windows - BitLocker Encryption]: ").strip() or "Windows - BitLocker Encryption"
    desc = input("Description [Full disk encryption with TPM and recovery key backup]: ").strip() or "Full disk encryption with TPM and recovery key backup"

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    BASE = "device_vendor_msft_bitlocker_systemdrivesrequirestartupauthentication"

    payload = {
        "name":         name,
        "description":  desc,
        "platforms":    "windows10",
        "technologies": "mdm",
        "settings": [
            # Require device encryption
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_bitlocker_requiredeviceencryption",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_bitlocker_requiredeviceencryption_1",
                        "children": []
                    }
                }
            },
            # Require encryption on fixed drives
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_bitlocker_fixeddrivesrequireencryption",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_bitlocker_fixeddrivesrequireencryption_1",
                        "children": []
                    }
                }
            },
            # Require startup authentication with all 5 required children
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": BASE,
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": f"{BASE}_1",
                        "children": [
                            # Non-TPM startup key: Blocked (_0)
                            {
                                "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                                "settingDefinitionId": f"{BASE}_configurenontpmstartupkeyusage_name",
                                "choiceSettingValue": {
                                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                                    "value": f"{BASE}_configurenontpmstartupkeyusage_name_0",
                                    "children": []
                                }
                            },
                            # TPM usage: Required (_1)
                            {
                                "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                                "settingDefinitionId": f"{BASE}_configuretpmusagedropdown_name",
                                "choiceSettingValue": {
                                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                                    "value": f"{BASE}_configuretpmusagedropdown_name_1",
                                    "children": []
                                }
                            },
                            # TPM PIN usage: Allowed (_2)
                            {
                                "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                                "settingDefinitionId": f"{BASE}_configurepinusagedropdown_name",
                                "choiceSettingValue": {
                                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                                    "value": f"{BASE}_configurepinusagedropdown_name_2",
                                    "children": []
                                }
                            },
                            # TPM startup key usage: Allowed (_2)
                            {
                                "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                                "settingDefinitionId": f"{BASE}_configuretpmstartupkeyusagedropdown_name",
                                "choiceSettingValue": {
                                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                                    "value": f"{BASE}_configuretpmstartupkeyusagedropdown_name_2",
                                    "children": []
                                }
                            },
                            # TPM PIN+key usage: Allowed (_2)
                            {
                                "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                                "settingDefinitionId": f"{BASE}_configuretpmpinkeyusagedropdown_name",
                                "choiceSettingValue": {
                                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                                    "value": f"{BASE}_configuretpmpinkeyusagedropdown_name_2",
                                    "children": []
                                }
                            },
                        ]
                    }
                }
            },
        ]
    }

    url     = "https://graph.microsoft.com/beta/deviceManagement/configurationPolicies"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\nCreating '{name}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! BitLocker profile created.")
        print(f"Name: {data.get('name')}")
        print(f"ID:   {data.get('id')}")
        print(f"\nℹ️  Recovery keys will be escrowed to Azure AD automatically.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_bitlocker()
    except Exception as e:
        print(f"Critical error: {e}")
