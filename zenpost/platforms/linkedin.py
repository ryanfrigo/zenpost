"""LinkedIn posting via API."""
import json
import requests
from ..config import get_platform_creds

API_BASE = "https://api.linkedin.com/v2"


def _headers() -> dict:
    creds = get_platform_creds("linkedin")
    if not creds.get("access_token"):
        raise Exception("LinkedIn not configured. Run: zenpost auth linkedin")
    return {
        "Authorization": f"Bearer {creds['access_token']}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _get_person_id() -> str:
    creds = get_platform_creds("linkedin")
    if creds.get("person_id"):
        return creds["person_id"]
    # Fetch from API
    r = requests.get(f"{API_BASE}/userinfo", headers=_headers())
    r.raise_for_status()
    return r.json()["sub"]


def _upload_image(image_path: str, person_id: str) -> str:
    """Upload image and return asset URN."""
    headers = _headers()
    
    # Register upload
    register_body = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": f"urn:li:person:{person_id}",
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent",
                }
            ],
        }
    }
    r = requests.post(
        f"{API_BASE}/assets?action=registerUpload",
        headers=headers,
        json=register_body,
    )
    r.raise_for_status()
    data = r.json()
    
    upload_url = data["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]
    asset = data["value"]["asset"]
    
    # Upload binary
    with open(image_path, "rb") as f:
        r = requests.put(
            upload_url,
            headers={"Authorization": headers["Authorization"]},
            data=f,
        )
        r.raise_for_status()
    
    return asset


def post(text: str, image_path: str = None) -> dict:
    """Post to LinkedIn feed."""
    person_id = _get_person_id()
    headers = _headers()
    
    body = {
        "author": f"urn:li:person:{person_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    
    if image_path:
        asset = _upload_image(image_path, person_id)
        content = body["specificContent"]["com.linkedin.ugc.ShareContent"]
        content["shareMediaCategory"] = "IMAGE"
        content["media"] = [
            {
                "status": "READY",
                "media": asset,
            }
        ]
    
    r = requests.post(f"{API_BASE}/ugcPosts", headers=headers, json=body)
    r.raise_for_status()
    post_id = r.json().get("id", "unknown")
    
    return {
        "id": post_id,
        "text": text,
        "url": f"https://www.linkedin.com/feed/update/{post_id}/",
    }
