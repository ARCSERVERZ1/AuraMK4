# app/services/google_drive.py

import os
import io
import pickle
import mimetypes
from typing import List, Dict, Optional, Union

# --- NEW IMPORTS FOR PROXY FIX ---
import httplib2
from google_auth_httplib2 import AuthorizedHttp
# ---------------------------------

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from google.auth.transport.requests import Request

os.environ["http_proxy"] = "http://proxy.server:3128"
os.environ["https_proxy"] = "http://proxy.server:3128"


class GoogleDriveStorage:
    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(
            self,
            credentials_file="/home/AuraEngine/AuraMK4/DOCMA/credentials.json",
            token_file="/home/AuraEngine/AuraMK4/DOCMA/token.pickle"
    ):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = self._login()

    def _login(self):
        creds = None

        # Load token
        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as token:
                creds = pickle.load(token)

        try:
            # If no creds → force login
            if not creds:
                print("❌ No credentials found (token missing). Switching to safe mode.")
                raise Exception("No credentials")

            # If expired → try refresh
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())

        except Exception as e:
            print("❌ Token invalid / expired:", str(e))

            if os.path.exists(self.token_file):
                os.remove(self.token_file)
                print("🗑️ Old token deleted")

            print("CURRENT WORKING DIRECTORY:", os.getcwd())
            print("CREDENTIAL PATH:", self.credentials_file)
            print("ABSOLUTE PATH:", os.path.abspath(self.credentials_file))
            print("TOKEN PATH:", self.token_file)
            print("TOKEN ABSOLUTE PATH:", os.path.abspath(self.token_file))

            # =====================================================
            # SAFE SERVER MODE (NO BROWSER CRASH)
            # =====================================================
            try:
                if not os.path.exists(self.credentials_file):
                    print("\n❌ credentials.json NOT FOUND")
                    print("👉 Place file at:", self.credentials_file)
                    return None  # IMPORTANT: no crash

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file,
                    self.SCOPES
                )

                creds = flow.run_local_server(
                    port=0,
                    access_type='offline',
                    prompt='consent'
                )

                with open(self.token_file, "wb") as token:
                    pickle.dump(creds, token)

            except Exception as web_error:
                print("\n❌ Google Drive AUTH FAILED (SERVER MODE)")
                print("DETAIL:", str(web_error))
                return None  # 🔥 IMPORTANT: DO NOT CRASH

        # =====================================================
        # THE FIX: HARDCODED HTTP PROXY FOR WSGI
        # =====================================================
        try:
            # 1. Hardcode the PythonAnywhere Free Tier Proxy
            proxy_info = httplib2.ProxyInfo(
                proxy_type=httplib2.socks.PROXY_TYPE_HTTP,
                proxy_host='proxy.server',
                proxy_port=3128
            )
            http_transport = httplib2.Http(proxy_info=proxy_info)

            # 2. Attach credentials to this proxy-enabled HTTP client
            authed_http = AuthorizedHttp(creds, http=http_transport)

            # 3. Build Drive service using the proxy HTTP client instead of the default
            return build("drive", "v3", http=authed_http)

        except Exception as final_error:
            print("❌ Google Drive service not initialized:", str(final_error))
            return None

    # =====================================================
    # CREATE / GET FOLDER
    # =====================================================
    def _get_or_create_folder(self, folder_name, parent_id=None):
        q = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            q += f" and '{parent_id}' in parents"

        result = self.service.files().list(q=q, fields="files(id,name)").execute()
        files = result.get("files", [])

        if files:
            return files[0]["id"]

        body = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder"
        }
        if parent_id:
            body["parents"] = [parent_id]

        folder = self.service.files().create(body=body, fields="id").execute()
        return folder["id"]

    # =====================================================
    # FIND FOLDER ONLY (NO CREATE)
    # =====================================================
    def _find_folder(self, folder_name, parent_id=None):
        q = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            q += f" and '{parent_id}' in parents"

        result = self.service.files().list(q=q, fields="files(id,name)").execute()
        files = result.get("files", [])
        return files[0]["id"] if files else None

    # =====================================================
    # CREATE PATH
    # =====================================================
    def _resolve_folder_path(self, folder_path):
        if not folder_path:
            return None
        parent_id = None
        for part in folder_path.split("/"):
            part = part.strip()
            if not part:
                continue
            parent_id = self._get_or_create_folder(part, parent_id)
        return parent_id

    # =====================================================
    # FIND PATH ONLY
    # =====================================================
    def _find_folder_path(self, folder_path):
        if not folder_path:
            return None
        parent_id = None
        for part in folder_path.split("/"):
            part = part.strip()
            if not part:
                continue
            parent_id = self._find_folder(part, parent_id)
            if not parent_id:
                return None
        return parent_id

    # =====================================================
    # SPLIT ABSOLUTE FILE PATH
    # =====================================================
    def _split_path(self, full_path):
        full_path = full_path.strip("/")
        parts = full_path.split("/")
        file_name = parts[-1]
        folder_path = "/".join(parts[:-1])
        return folder_path, file_name

    # =====================================================
    # UPLOAD MULTIPLE FILES TO TARGET FOLDER
    # =====================================================
    def upload_files(self, files: List[Union[str, object]], target_folder=""):
        parent_id = self._resolve_folder_path(target_folder)
        results = []
        for file_item in files:
            try:
                result = self._upload_single(file_item, parent_id)
                results.append(result)
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        return results

    # =====================================================
    # INTERNAL UPLOAD
    # =====================================================
    def _upload_single(self, file_item, parent_id=None):
        if isinstance(file_item, str):
            file_name = os.path.basename(file_item)
            mime_type = mimetypes.guess_type(file_item)[0]
            media = MediaFileUpload(file_item, mimetype=mime_type, resumable=True)
        else:
            file_name = file_item.name
            mime_type = file_item.content_type
            media = MediaIoBaseUpload(io.BytesIO(file_item.read()), mimetype=mime_type, resumable=True)

        body = {"name": file_name}
        if parent_id:
            body["parents"] = [parent_id]

        file = self.service.files().create(
            body=body,
            media_body=media,
            fields="id,name"
        ).execute()

        self.make_public(file["id"])

        return {
            "success": True,
            "id": file["id"],
            "name": file["name"],
            "image_url": f"https://drive.google.com/uc?id={file['id']}"
        }

    # =====================================================
    # MAKE PUBLIC
    # =====================================================
    def make_public(self, file_id):
        self.service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"}
        ).execute()

    # =====================================================
    # GET FILE BY ABSOLUTE PATH
    # =====================================================
    def get_file(self, full_path):
        folder_path, file_name = self._split_path(full_path)
        parent_id = self._find_folder_path(folder_path)
        if folder_path and not parent_id:
            return None
        q = f"name='{file_name}' and trashed=false"
        if parent_id:
            q += f" and '{parent_id}' in parents"

        result = self.service.files().list(q=q, fields="files(id,name,mimeType,webViewLink)").execute()
        files = result.get("files", [])
        return files[0] if files else None

    # =====================================================
    # LIST FILES BY FOLDER PATH
    # =====================================================
    def list_files(self, folder_path=""):
        parent_id = self._find_folder_path(folder_path)
        if folder_path and not parent_id:
            return []
        q = "trashed=false"
        if parent_id:
            q += f" and '{parent_id}' in parents"

        result = self.service.files().list(q=q, fields="files(id,name,mimeType,webViewLink)").execute()
        return result.get("files", [])

    # =====================================================
    # DELETE BY ABSOLUTE PATH
    # =====================================================
    def delete_by_path(self, full_path):
        file = self.get_file(full_path)
        if not file:
            return False
        self.service.files().delete(fileId=file["id"]).execute()
        return True

    # =====================================================
    # RENAME BY PATH
    # =====================================================
    def rename_by_path(self, old_path, new_file_name):
        file = self.get_file(old_path)
        if not file:
            return False
        self.service.files().update(
            fileId=file["id"],
            body={"name": new_file_name}
        ).execute()
        return True

    # =====================================================
    # UPDATE FILE CONTENT BY PATH
    # =====================================================
    def update_file(self, full_path, new_local_file):
        file = self.get_file(full_path)
        if not file:
            return False
        mime_type = mimetypes.guess_type(new_local_file)[0]
        media = MediaFileUpload(new_local_file, mimetype=mime_type, resumable=True)
        self.service.files().update(
            fileId=file["id"],
            media_body=media
        ).execute()
        return True