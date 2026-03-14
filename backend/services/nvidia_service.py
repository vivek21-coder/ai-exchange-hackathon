import os
import uuid
import base64
import requests
import logging
from fastapi import HTTPException

logger = logging.getLogger("learncast.nvidia")

INVOKE_URL = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell"


def generate_image(prompt: str) -> str:
    """Generate an image from a prompt using NVIDIA's Flux.1-schnell API.
    Saves the image as a JPEG and returns the file path."""
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="NVIDIA_API_KEY is not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    # Vertical image for reels (roughly 9:16)
    # NVIDIA's Flux API usually supports 1024x1024, or fixed ratios.
    # We will use 1024x1024 and then crop it in video_service to fit 720x1280.
    payload = {
        "prompt": prompt,
        "width": 1024,
        "height": 1024,
        "seed": 0,
        "steps": 4
    }

    logger.info("Generating image with prompt: %s", prompt[:100] + "...")
    try:
        response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        # The response structure from NVIDIA's Flux.1-schnell can vary, but based on the snippet:
        # data might contain a list of artifacts or a base64 encoded image.
        # Based on typical NVIDIA GenAI responses, it's often in data['artifacts'][0]['base64']
        # Let's check the snippet provided: response_body = response.json(); print(response_body)
        
        # In case it's in a different format, we'll try to find the b64 string
        # Typically for Flux on NVIDIA it is:
        # {
        #   "artifacts": [
        #     {
        #       "base64": "...",
        #       "seed": 0,
        #       "finishReason": "SUCCESS"
        #     }
        #   ]
        # }
        
        artifacts = data.get("artifacts", [])
        if not artifacts:
            # Maybe it's directly in 'b64_json' (OpenAI style)
            b64_str = data.get("b64_json")
        else:
            b64_str = artifacts[0].get("base64")

        if not b64_str:
             logger.error("NVIDIA API response missing image data: %s", str(data)[:500])
             raise HTTPException(status_code=502, detail="NVIDIA API returned no image data")

        image_data = base64.b64decode(b64_str)
        
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"image_{uuid.uuid4().hex[:12]}.jpg"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "wb") as f:
            f.write(image_data)

        logger.info("Image saved to: %s (size: %.1f KB)", filepath, len(image_data) / 1024)
        return filepath

    except Exception as e:
        logger.error("NVIDIA image generation failed: %s", str(e))
        # We don't want to crash the whole reel if one image fails.
        # Return None and the video service can use a fallback (e.g. solid color)
        return None
