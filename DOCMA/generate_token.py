# generate_token.py

import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive.file"
]

flow = InstalledAppFlow.from_client_secrets_file(
    "credentials.json",
    SCOPES
)

creds = flow.run_local_server(
    port=0,
    access_type="offline",
    prompt="consent"
)

with open("token.pickle", "wb") as token:
    pickle.dump(creds, token)

print("✅ token.pickle created")