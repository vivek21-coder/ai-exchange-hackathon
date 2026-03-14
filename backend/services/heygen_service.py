import os
import requests
from fastapi import HTTPException

HEYGEN_BASE_URL = "https://api.heygen.com"


def _get_headers():
    api_key = os.getenv("HEYGEN_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="HEYGEN_API_KEY is not set")
    return {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
    }


def create_video(script: str, language: str) -> dict:
    url = f"{HEYGEN_BASE_URL}/v2/video/generate"
    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": "Abigail_expressive_2024112501",
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": "1bd001e7e50f421d891986aad5158bc8",
                    "speed": 1.05,
                },
                "background": {
                    "type": "color",
                    "value": "#0f0f1a",
                },
            }
        ],
        "dimension": {"width": 720, "height": 1280},
        "aspect_ratio": "9:16",
        "caption": True,
        "test": True,
    }

    try:
        resp = requests.post(url, json=payload, headers=_get_headers(), timeout=30)
        data = resp.json()

        if resp.status_code == 200 and data.get("data", {}).get("video_id"):
            return {"job_id": data["data"]["video_id"]}

        raise HTTPException(
            status_code=502,
            detail=f"HeyGen video creation failed: {str(data)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"HeyGen video creation failed: {str(e)}",
        )


def get_video_status(job_id: str) -> dict:
    url = f"{HEYGEN_BASE_URL}/v1/video_status.get?video_id={job_id}"

    try:
        resp = requests.get(url, headers=_get_headers(), timeout=15)
        data = resp.json().get("data", {})
        status = data.get("status", "")

        if status == "completed":
            return {"status": "completed", "video_url": data.get("video_url")}
        elif status in ("processing", "pending"):
            return {"status": "processing", "video_url": None}
        elif status == "failed":
            return {"status": "failed", "video_url": None}
        else:
            return {"status": "processing", "video_url": None}
    except Exception:
        return {"status": "processing", "video_url": None}
