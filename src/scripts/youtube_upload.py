import os
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def must_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v

def main() -> int:
    client_id = must_env("YT_CLIENT_ID")
    client_secret = must_env("YT_CLIENT_SECRET")
    refresh_token = must_env("YT_REFRESH_TOKEN")

    video_path = must_env("VIDEO_PATH")
    title = os.getenv("VIDEO_TITLE", "Upload test via GitHub Actions")
    description = os.getenv("VIDEO_DESCRIPTION", "Automated upload test")
    privacy_status = os.getenv("VIDEO_PRIVACY", "unlisted")  # private|unlisted|public

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "22",  # People & Blogs (safe default)
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    req = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    print("Upload complete. Video ID:", resp.get("id"))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print("ERROR:", str(e), file=sys.stderr)
        raise
