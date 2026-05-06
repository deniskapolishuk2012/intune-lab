import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import math
import zipfile
import base64
import xml.etree.ElementTree as ET
import requests
from core.auth import get_access_token

CHUNK_SIZE = 5 * 1024 * 1024  # 5MB

# Known app configs — auto-applied when setup file name matches
KNOWN_APPS = {
    "7z2407-x64.msi": {
        "displayName":      "7-Zip 24.07",
        "description":      "7-Zip file archiver",
        "publisher":        "Igor Pavlov",
        "installCommand":   "msiexec /i 7z2407-x64.msi /qn /norestart",
        "uninstallCommand": "msiexec /x {23170F69-40C1-2702-2407-000001000000} /qn /norestart",
        "detectionRules": [{
            "@odata.type":            "#microsoft.graph.win32LobAppProductCodeDetection",
            "productCode":             "{23170F69-40C1-2702-2407-000001000000}",
            "productVersion":          "24.07.0.0",
            "productVersionOperator":  "greaterThanOrEqual"
        }]
    },
    "npp.8.6.7.installer.x64.exe": {
        "displayName":      "Notepad++ 8.6.7 (x64)",
        "description":      "Notepad++ text editor",
        "publisher":        "Notepad++ Team",
        "installCommand":   "npp.8.6.7.Installer.x64.exe /S",
        "uninstallCommand": "C:\\Program Files\\Notepad++\\uninstall.exe /S",
        "detectionRules": [{
            "@odata.type":            "#microsoft.graph.win32LobAppFileSystemDetection",
            "path":                    "C:\\Program Files\\Notepad++",
            "fileOrFolderName":        "notepad++.exe",
            "check32BitOn64System":    False,
            "detectionType":           "exists",
            "operator":               "notConfigured",
        }]
    },
}

def find_intunewin_files(folder: str) -> list:
    """Scans a folder for .intunewin files."""
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith('.intunewin')
    ]

def parse_intunewin(filepath: str) -> dict:
    """Extracts metadata and encrypted content from .intunewin file."""
    with zipfile.ZipFile(filepath, 'r') as z:
        with z.open('IntuneWinPackage/Metadata/Detection.xml') as f:
            content = f.read().decode('utf-8')
            root    = ET.fromstring(content)

        def get(tag):
            for el in root.iter():
                if el.tag.split('}')[-1] == tag:
                    return el.text
            return None

        inner_path = os.path.join(os.environ.get('TEMP', os.getcwd()), os.path.basename(filepath) + '.pkg')
        with z.open('IntuneWinPackage/Contents/IntunePackage.intunewin') as src:
            with open(inner_path, 'wb') as dst:
                dst.write(src.read())

        return {
            "setupFile":            get('SetupFile'),
            "appName":              get('Name'),
            "encryptionKey":        get('EncryptionKey'),
            "macKey":               get('MacKey'),
            "initializationVector": get('InitializationVector'),
            "mac":                  get('Mac'),
            "profileIdentifier":    get('ProfileIdentifier'),
            "fileDigest":           get('FileDigest'),
            "fileDigestAlgorithm":  get('FileDigestAlgorithm'),
            "unencryptedSize":      int(get('UnencryptedContentSize') or 0),
            "encryptedFilePath":    inner_path,
            "encryptedSize":        os.path.getsize(inner_path),
        }

def get_app_config(meta: dict) -> dict:
    """
    Returns app config — from KNOWN_APPS if recognized,
    otherwise prompts user to enter details interactively.
    """
    setup_file = (meta.get("setupFile") or "").lower()

    # Check known apps
    for key, config in KNOWN_APPS.items():
        if key in setup_file:
            print(f"  ✅ Recognized app: {config['displayName']} — using preset config.")
            return {**config, "fileName": meta["setupFile"]}

    # Unknown app — ask user
    print(f"\n  Unknown app: {meta['appName']}")
    print(f"  Setup file:  {meta['setupFile']}")
    print(f"  Please provide installation details:\n")

    display_name      = input(f"  Display name [{meta['appName']}]: ").strip() or meta['appName']
    publisher         = input(f"  Publisher: ").strip() or "Unknown"
    description       = input(f"  Description (optional): ").strip() or display_name
    install_command   = input(f"  Install command (e.g. setup.exe /S): ").strip()
    uninstall_command = input(f"  Uninstall command: ").strip()

    print(f"\n  Detection rule type:")
    print(f"    1. File/Folder exists (recommended for EXE apps)")
    print(f"    2. Registry key exists")
    det_choice = input(f"  Choose [1]: ").strip() or "1"

    if det_choice == "2":
        reg_key   = input("  Registry key path: ").strip()
        reg_value = input("  Registry value name (optional): ").strip()
        detection = [{
            "@odata.type":         "#microsoft.graph.win32LobAppRegistryDetection",
            "keyPath":              reg_key,
            "valueName":            reg_value,
            "check32BitOn64System": False,
            "detectionType":        "exists",
            "operator":             "notConfigured",
            "detectionValue":       None
        }]
    else:
        det_path = input("  Detection folder path (e.g. C:\\Program Files\\AppName): ").strip()
        det_file = input("  Detection file name (e.g. app.exe): ").strip()
        detection = [{
            "@odata.type":          "#microsoft.graph.win32LobAppFileSystemDetection",
            "path":                  det_path,
            "fileOrFolderName":      det_file,
            "check32BitOn64System":  False,
            "detectionType":         "exists",
            "operator":              "notConfigured",
            "detectionValue":        None
        }]

    return {
        "displayName":      display_name,
        "description":      description,
        "publisher":        publisher,
        "fileName":         meta["setupFile"],
        "installCommand":   install_command,
        "uninstallCommand": uninstall_command,
        "detectionRules":   detection,
    }

def create_app(token: str, config: dict, meta: dict) -> str | None:
    url     = "https://graph.microsoft.com/beta/deviceAppManagement/mobileApps"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {
        "@odata.type":          "#microsoft.graph.win32LobApp",
        "displayName":           config["displayName"],
        "description":           config["description"],
        "publisher":             config["publisher"],
        "fileName":              config["fileName"],
        "installCommandLine":    config["installCommand"],
        "uninstallCommandLine":  config["uninstallCommand"],
        "applicableArchitectures": "x64",
        "minimumSupportedOperatingSystem": {
            "@odata.type": "#microsoft.graph.windowsMinimumOperatingSystem",
            "v10_1607": True
        },
        "installExperience": {
            "@odata.type":           "#microsoft.graph.win32LobAppInstallExperience",
            "runAsAccount":           "system",
            "deviceRestartBehavior":  "suppress"
        },
        "detectionRules":   config["detectionRules"],
        "requirementRules": [],
        "setupFilePath":    config["fileName"],
    }

    # msiInformation only for MSI installers
    if config["fileName"].lower().endswith(".msi"):
        payload["msiInformation"] = None

    import json as _j
    print(f"  App payload:\n{_j.dumps(payload, indent=2)}")
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        return response.json().get("id")
    print(f"❌ Failed to create app (HTTP {response.status_code}):")
    print(response.text)
    return None

def create_content_version(token: str, app_id: str) -> str | None:
    url     = f"https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/{app_id}/microsoft.graph.win32LobApp/contentVersions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(url, json={}, headers=headers)
    if response.status_code == 201:
        return response.json().get("id")
    print(f"❌ Failed to create content version (HTTP {response.status_code}):")
    print(response.text)
    return None

def create_file_entry(token: str, app_id: str, version_id: str, meta: dict, config: dict) -> str | None:
    url = (
        f"https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/{app_id}"
        f"/microsoft.graph.win32LobApp/contentVersions/{version_id}/files"
    )
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "@odata.type":  "#microsoft.graph.mobileAppContentFile",
        "name":          config["fileName"],
        "size":          meta["unencryptedSize"],
        "sizeEncrypted": meta["encryptedSize"],
        "isDependency":  False,
    }
    # Remove @odata.type — some tenants reject it in file entry
    del payload["@odata.type"]
    import json as _j2
    print(f"  File entry payload: {_j2.dumps(payload)}")
    print(f"  URL: {url}")
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        return response.json().get("id")
    print(f"❌ Failed to create file entry (HTTP {response.status_code}):")
    print(response.text)
    return None

def wait_for_storage_uri(token: str, app_id: str, version_id: str, file_id: str) -> str | None:
    import time
    url     = (
        f"https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/{app_id}"
        f"/microsoft.graph.win32LobApp/contentVersions/{version_id}/files/{file_id}"
    )
    headers = {"Authorization": f"Bearer {token}"}
    for i in range(20):
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            uri = resp.json().get("azureStorageUri")
            if uri:
                return uri
        time.sleep(3)
        print(f"  Waiting for storage URI... ({i+1}/20)")
    print("❌ Timed out.")
    return None

def upload_to_azure(storage_uri: str, filepath: str) -> bool:
    file_size  = os.path.getsize(filepath)
    num_chunks = math.ceil(file_size / CHUNK_SIZE)
    block_ids  = []

    print(f"  Uploading {file_size:,} bytes in {num_chunks} chunk(s)...")
    with open(filepath, 'rb') as f:
        for i in range(num_chunks):
            chunk    = f.read(CHUNK_SIZE)
            block_id = base64.b64encode(f"{i:05d}".encode()).decode()
            block_ids.append(block_id)
            url  = f"{storage_uri}&comp=block&blockid={block_id}"
            resp = requests.put(url, data=chunk, headers={
                "x-ms-blob-type": "BlockBlob",
                "Content-Type":   "application/octet-stream",
            })
            if resp.status_code != 201:
                print(f"❌ Chunk {i} failed (HTTP {resp.status_code})")
                return False
            print(f"  Chunk {i+1}/{num_chunks} ✓")

    xml = '<?xml version="1.0" encoding="utf-8"?><BlockList>' + \
          ''.join(f'<Latest>{b}</Latest>' for b in block_ids) + '</BlockList>'
    resp = requests.put(f"{storage_uri}&comp=blocklist", data=xml.encode(),
                        headers={"Content-Type": "application/xml"})
    if resp.status_code == 201:
        print("  ✅ Upload complete.")
        return True
    print(f"❌ Block commit failed (HTTP {resp.status_code})")
    return False

def commit_file(token: str, app_id: str, version_id: str, file_id: str, meta: dict) -> bool:
    url = (
        f"https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/{app_id}"
        f"/microsoft.graph.win32LobApp/contentVersions/{version_id}/files/{file_id}"
        f"/commit"
    )
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "fileEncryptionInfo": {
            "@odata.type":         "#microsoft.graph.fileEncryptionInfo",
            "encryptionKey":        meta["encryptionKey"],
            "macKey":               meta["macKey"],
            "initializationVector": meta["initializationVector"],
            "mac":                  meta["mac"],
            "profileIdentifier":    meta["profileIdentifier"],
            "fileDigest":           meta["fileDigest"],
            "fileDigestAlgorithm":  meta["fileDigestAlgorithm"],
        }
    }
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code not in (200, 201, 204):
        print(f"❌ Commit HTTP {resp.status_code}: {resp.text}")
        return False
    return True

def wait_for_commit(token: str, app_id: str, version_id: str, file_id: str) -> bool:
    import time
    url     = (
        f"https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/{app_id}"
        f"/microsoft.graph.win32LobApp/contentVersions/{version_id}/files/{file_id}"
    )
    headers = {"Authorization": f"Bearer {token}"}
    for i in range(30):
        resp  = requests.get(url, headers=headers)
        state = resp.json().get("uploadState", "") if resp.status_code == 200 else ""
        if state == "commitFileSuccess":
            return True
        if "fail" in state.lower():
            print(f"❌ Commit failed: {state}")
            return False
        time.sleep(5)
        print(f"  Waiting for commit... ({i+1}/30) state: {state}")
    print("❌ Timed out.")
    return False

def finalize_app(token: str, app_id: str, version_id: str) -> bool:
    url     = f"https://graph.microsoft.com/beta/deviceAppManagement/mobileApps/{app_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "@odata.type":             "#microsoft.graph.win32LobApp",
        "committedContentVersion": version_id
    }
    resp = requests.patch(url, json=payload, headers=headers)
    return resp.status_code in (200, 201, 204)

def upload_win32_app():
    """
    Uploads any .intunewin file to Intune.
    - Known apps (7-Zip, Notepad++) are auto-configured.
    - Unknown apps prompt for install/detection details.
    - Scans a folder OR accepts a direct file path.
    """
    print("\n=== Microsoft Graph: Upload Win32 App to Intune ===")

    path_input = input("\nPath to .intunewin file or folder containing .intunewin files:\n> ").strip().strip('"')

    # Resolve file path
    if os.path.isdir(path_input):
        files = find_intunewin_files(path_input)
        if not files:
            print(f"❌ No .intunewin files found in: {path_input}")
            return
        print(f"\nFound {len(files)} .intunewin file(s):")
        for i, f in enumerate(files, start=1):
            print(f"  {i}. {os.path.basename(f)}")
        choice = input("\nEnter number to upload: ").strip()
        try:
            intunewin_path = files[int(choice) - 1]
        except (ValueError, IndexError):
            print("❌ Invalid choice.")
            return
    elif os.path.isfile(path_input) and path_input.lower().endswith('.intunewin'):
        intunewin_path = path_input
    else:
        print(f"❌ Not a valid .intunewin file or folder: {path_input}")
        return

    token = get_access_token()
    if not token:
        print("❌ Error: Could not obtain an access token.")
        return

    print(f"\n[1/6] Parsing {os.path.basename(intunewin_path)}...")
    meta = parse_intunewin(intunewin_path)
    print(f"  Setup file:     {meta['setupFile']}")
    print(f"  Encrypted size: {meta['encryptedSize']:,} bytes")

    print(f"\n[2/6] Resolving app config...")
    config = get_app_config(meta)

    print(f"\n[3/6] Creating app entry '{config['displayName']}' in Intune...")
    app_id = create_app(token, config, meta)
    if not app_id:
        return
    print(f"  App ID: {app_id}")

    print(f"\n[4/6] Creating content version...")
    version_id = create_content_version(token, app_id)
    if not version_id:
        return

    print(f"\n[5/6] Creating file entry...")
    file_id = create_file_entry(token, app_id, version_id, meta, config)
    if not file_id:
        return

    print(f"\n  Waiting for Azure Storage URI...")
    storage_uri = wait_for_storage_uri(token, app_id, version_id, file_id)
    if not storage_uri:
        return

    print(f"\n  Uploading to Azure Blob Storage...")
    if not upload_to_azure(storage_uri, meta["encryptedFilePath"]):
        return

    print(f"\n  Committing with encryption info...")
    if not commit_file(token, app_id, version_id, file_id, meta):
        print("❌ Commit failed.")
        return

    print(f"\n  Waiting for commit confirmation...")
    if not wait_for_commit(token, app_id, version_id, file_id):
        return

    print(f"\n[6/6] Finalizing app...")
    if finalize_app(token, app_id, version_id):
        print(f"\n✅ Success! '{config['displayName']}' uploaded to Intune.")
        print(f"App ID: {app_id}")
        print(f"\nNext: run assign_app.py to assign to a group.")
    else:
        print("❌ Finalization failed.")

if __name__ == "__main__":
    try:
        upload_win32_app()
    except Exception as e:
        import traceback
        print(f"Critical error: {e}")
        traceback.print_exc()
