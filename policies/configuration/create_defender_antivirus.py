import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import requests
from core.auth import get_access_token

def create_defender_antivirus():
    """
    Creates a Microsoft Defender Antivirus configuration profile
    using the Settings Catalog API.

    NOTE: configurationPolicies requires the beta endpoint.
    https://graph.microsoft.com/beta/deviceManagement/configurationPolicies

    Settings configured:
    - Real-time protection: ON
    - Cloud-delivered protection: ON (High level)
    - Automatic sample submission: Send safe samples
    - Behavior monitoring: ON
    - Archive file scanning: ON
    - PUA (Potentially Unwanted Apps): Block
    """
    print("\n=== TEST: Create Profile via Settings Catalog API ===")
    print("Profile: Microsoft Defender Antivirus")
    print("Endpoint: /beta/deviceManagement/configurationPolicies\n")

    name = input("Profile name [Windows - Defender Antivirus]: ").strip()
    if not name:
        name = "Windows - Defender Antivirus"

    desc = input("Description [Defender AV real-time and cloud protection]: ").strip()
    if not desc:
        desc = "Defender AV real-time and cloud protection"

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    payload = {
        "name":         name,
        "description":  desc,
        "platforms":    "windows10",
        "technologies": "mdm,microsoftSense",
        "settings": [
            # Real-time protection: ON
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_defender_allowrealtimemonitoring",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_defender_allowrealtimemonitoring_1"
                    }
                }
            },
            # Behavior monitoring: ON
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_defender_allowbehaviormonitoring",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_defender_allowbehaviormonitoring_1"
                    }
                }
            },
            # Cloud-delivered protection: ON
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_defender_allowcloudprotection",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_defender_allowcloudprotection_1"
                    }
                }
            },
            # Cloud protection level: High
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_defender_cloudblocklevel",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_defender_cloudblocklevel_2"
                    }
                }
            },
            # Automatic sample submission: Send safe samples
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_defender_submitsamplesconsent",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_defender_submitsamplesconsent_1"
                    }
                }
            },
            # Scan archive files: ON
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_defender_allowarchivescanning",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_defender_allowarchivescanning_1"
                    }
                }
            },
            # PUA protection: Block
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_defender_puaprotection",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_defender_puaprotection_1"
                    }
                }
            },
        ]
    }

    # Settings Catalog requires beta endpoint
    url     = "https://graph.microsoft.com/beta/deviceManagement/configurationPolicies"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    print(f"Creating '{name}'...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print(f"\n✅ Success! Settings Catalog API works correctly.")
        print(f"Name: {data.get('name')}")
        print(f"ID:   {data.get('id')}")
        print(f"\nReady to build the remaining configuration profiles.")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_defender_antivirus()
    except Exception as e:
        print(f"Critical error: {e}")
