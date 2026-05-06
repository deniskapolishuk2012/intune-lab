import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import requests
from core.auth import get_access_token

def create_firewall():
    """
    Creates a Windows Firewall configuration profile via Settings Catalog API.

    Settings configured:
    - Domain profile firewall: ON
    - Private profile firewall: ON
    - Public profile firewall: ON
    - Inbound connections: Block by default (all profiles)
    - Inbound notifications: Disabled (no popup asking user to allow)
    """
    print("\n=== Create Profile: Windows Firewall ===")

    name = input("Profile name [Windows - Firewall]: ").strip() or "Windows - Firewall"
    desc = input("Description [Firewall enabled on all network profiles]: ").strip() or "Firewall enabled on all network profiles"

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
            # Domain profile — Enable firewall
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "vendor_msft_firewall_mdmstore_domainprofile_enablefirewall",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "vendor_msft_firewall_mdmstore_domainprofile_enablefirewall_true"
                    }
                }
            },
            # Domain profile — Block inbound by default
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "vendor_msft_firewall_mdmstore_domainprofile_defaultinboundaction",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "vendor_msft_firewall_mdmstore_domainprofile_defaultinboundaction_1"
                    }
                }
            },
            # Private profile — Enable firewall
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "vendor_msft_firewall_mdmstore_privateprofile_enablefirewall",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "vendor_msft_firewall_mdmstore_privateprofile_enablefirewall_true"
                    }
                }
            },
            # Private profile — Block inbound by default
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "vendor_msft_firewall_mdmstore_privateprofile_defaultinboundaction",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "vendor_msft_firewall_mdmstore_privateprofile_defaultinboundaction_1"
                    }
                }
            },
            # Public profile — Enable firewall
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "vendor_msft_firewall_mdmstore_publicprofile_enablefirewall",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "vendor_msft_firewall_mdmstore_publicprofile_enablefirewall_true"
                    }
                }
            },
            # Public profile — Block inbound by default
            {
                "settingInstance": {
                    "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingInstance",
                    "settingDefinitionId": "vendor_msft_firewall_mdmstore_publicprofile_defaultinboundaction",
                    "choiceSettingValue": {
                        "@odata.type": "#microsoft.graph.deviceManagementConfigurationChoiceSettingValue",
                        "value": "vendor_msft_firewall_mdmstore_publicprofile_defaultinboundaction_1"
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
        print(f"\n✅ Success! Firewall profile created.")
        print(f"Name: {data.get('name')}")
        print(f"ID:   {data.get('id')}")
    else:
        print(f"\n❌ Failed (HTTP {response.status_code}):")
        print(response.text)

if __name__ == "__main__":
    try:
        create_firewall()
    except Exception as e:
        print(f"Critical error: {e}")
