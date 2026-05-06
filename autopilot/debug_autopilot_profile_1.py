import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from core.auth import get_access_token

def debug_autopilot_profile():
    token = get_access_token()
    if not token:
        print("❌ No token.")
        return

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = "https://graph.microsoft.com/beta/deviceManagement/windowsAutopilotDeploymentProfiles"

    tests = [
        {
            "label": "Test 1: only hidePrivacySettings + hideEULA",
            "payload": {
                "@odata.type": "#microsoft.graph.azureADWindowsAutopilotDeploymentProfile",
                "displayName": "Debug Test 1",
                "outOfBoxExperienceSettings": {
                    "hidePrivacySettings": True,
                    "hideEULA": True,
                }
            }
        },
        {
            "label": "Test 2: only userType",
            "payload": {
                "@odata.type": "#microsoft.graph.azureADWindowsAutopilotDeploymentProfile",
                "displayName": "Debug Test 2",
                "outOfBoxExperienceSettings": {
                    "userType": "standard",
                }
            }
        },
        {
            "label": "Test 3: empty outOfBoxExperienceSettings",
            "payload": {
                "@odata.type": "#microsoft.graph.azureADWindowsAutopilotDeploymentProfile",
                "displayName": "Debug Test 3",
                "outOfBoxExperienceSettings": {}
            }
        },
        {
            "label": "Test 4: no outOfBoxExperienceSettings at all (just displayName worked before)",
            "payload": {
                "@odata.type": "#microsoft.graph.azureADWindowsAutopilotDeploymentProfile",
                "displayName": "Debug Test 4",
            }
        },
    ]

    for test in tests:
        print(f"\n{test['label']}")
        response = requests.post(url, json=test["payload"], headers=headers)
        print(f"  HTTP {response.status_code}")
        if response.status_code == 201:
            print(f"  ✅ SUCCESS!")
            print(f"  ID: {response.json().get('id')}")
        else:
            try:
                msg = response.json().get("error", {}).get("message", "")[:300]
                print(f"  ❌ {msg}")
            except:
                print(f"  ❌ {response.text[:300]}")

if __name__ == "__main__":
    debug_autopilot_profile()
