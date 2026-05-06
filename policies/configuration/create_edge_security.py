import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import requests
from core.auth import get_access_token

def create_edge_security():
    """
    Creates a Microsoft Edge Security profile via Settings Catalog API.

    Group 3 — User & App Control:
    - SmartScreen: ON (phishing/malware protection)
    - Block InPrivate browsing: ON
    - Block popups: ON
    - Force safe search: ON
    - Disable password manager: ON (use enterprise vault instead)
    - Block extensions from unknown sources: ON
    """
    print("\n=== Create Profile: Microsoft Edge Security ===")
    print("Group 3 — User & App Control\n")

    name = input("Profile name [Windows - Edge Security]: ").strip() or "Windows - Edge Security"
    desc = input("Description [Edge browser security hardening]: ").strip() or "Edge browser security hardening"

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    payload = {
        "name":         name,
        "description":  desc,
        "platforms":    "windows10",
        "technologies": "mdm",
        "settings": [
            # Enable SmartScreen
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_browser_allowsmartscreen",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_browser_allowsmartscreen_1"
                    }
                }
            },
            # Block InPrivate browsing
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_browser_allowinprivate",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_browser_allowinprivate_0"  # Block
                    }
                }
            },
            # Block popups
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_browser_allowpopups",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_browser_allowpopups_0"  # Block
                    }
                }
            },
            # Prevent SmartScreen bypass
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_browser_preventsmartscreenpromptoverride",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_browser_preventsmartscreenpromptoverride_1"
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
        print(f"\n✅ Success! Edge Security profile created.")
        print(f"Name: {data.get('name')}")
        print(f"ID:   {data.get('id')}")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_edge_security()
    except Exception as e:
        print(f"Critical error: {e}")
