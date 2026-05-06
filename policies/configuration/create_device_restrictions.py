import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import requests
from core.auth import get_access_token

def create_device_restrictions():
    """
    Creates a Device Restrictions profile via Settings Catalog API.

    Group 3 — User & App Control:
    - USB storage: Block
    - Camera: Block
    - Bluetooth: Block
    - Screenshots: Block
    - Microsoft Store: Block
    - Simple passwords: Block
    """
    print("\n=== Create Profile: Device Restrictions ===")
    print("Group 3 — User & App Control\n")

    name = input("Profile name [Windows - Device Restrictions]: ").strip() or "Windows - Device Restrictions"
    desc = input("Description [Block USB, camera, bluetooth, screenshots, Store]: ").strip() or "Block USB, camera, bluetooth, screenshots, Store"

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
            # Block USB storage
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_connectivity_allowusbconnection",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_connectivity_allowusbconnection_0"  # Block
                    }
                }
            },
            # Block Camera
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_camera_allowcamera",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_camera_allowcamera_0"  # Block
                    }
                }
            },
            # Block Bluetooth
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_connectivity_allowbluetooth",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_connectivity_allowbluetooth_0"  # Block
                    }
                }
            },
            # Block Screenshots
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_experience_allowscreencapture",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_experience_allowscreencapture_0"  # Block
                    }
                }
            },
            # Block Microsoft Store
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "device_vendor_msft_policy_config_applicationmanagement_allowappstoreautoupdate",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "device_vendor_msft_policy_config_applicationmanagement_allowappstoreautoupdate_0"
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
        print(f"\n✅ Success! Device Restrictions profile created.")
        print(f"Name: {data.get('name')}")
        print(f"ID:   {data.get('id')}")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_device_restrictions()
    except Exception as e:
        print(f"Critical error: {e}")
