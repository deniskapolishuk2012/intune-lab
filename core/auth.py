import os
import msal
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# === CONFIGURATION — loaded from .env file ===
# Copy .env.example to .env and fill in your values
CONFIG = {
    "TENANT_ID":     os.getenv("TENANT_ID",     ""),
    "CLIENT_ID":     os.getenv("CLIENT_ID",      ""),
    "CLIENT_SECRET": os.getenv("CLIENT_SECRET",  ""),
    "DOMAIN":        os.getenv("DOMAIN",         ""),
}

def get_access_token() -> str | None:
    """
    Authenticates against Microsoft Identity Platform using
    client credentials flow and returns a bearer token for
    Microsoft Graph API calls.
    Credentials are loaded from .env file.
    """
    # Validate config
    missing = [k for k, v in CONFIG.items() if not v]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print(f"   Copy .env.example to .env and fill in your values.")
        return None

    authority = f"https://login.microsoftonline.com/{CONFIG['TENANT_ID']}"
    app = msal.ConfidentialClientApplication(
        CONFIG['CLIENT_ID'],
        authority=authority,
        client_credential=CONFIG['CLIENT_SECRET']
    )
    result = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])

    if "access_token" not in result:
        error = result.get("error_description", "Unknown error")
        print(f"❌ Failed to get token: {error}")
        return None

    return result.get("access_token")
