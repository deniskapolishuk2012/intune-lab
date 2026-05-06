import requests
import json
from auth import get_access_token

def debug_skus():
    """
    Dumps all raw SKU data from your tenant so we can see
    exactly what fields and values the Graph API returns.
    """
    token = get_access_token()
    if not token:
        print("❌ Could not get token.")
        return

    url      = "https://graph.microsoft.com/v1.0/subscribedSkus"
    headers  = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    print(f"HTTP Status: {response.status_code}\n")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    debug_skus()
