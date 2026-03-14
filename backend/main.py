import os
import logging
import time
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services import claude_service, elevenlabs_service, video_service, nvidia_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("learncast")

load_dotenv()
os.makedirs("outputs", exist_ok=True)

app = FastAPI(title="LearnCast AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated video files
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


class GenerateRequest(BaseModel):
    topic: str
    language: str
    level: str


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    total_start = time.time()
    logger.info("="*60)
    logger.info("NEW REQUEST: topic=%r, language=%s, level=%s", req.topic, req.language, req.level)
    logger.info("="*60)

    # Step 1: Generate script and image prompts with Gemini
    logger.info("[Step 1/4] Generating script and image prompts with Gemini...")
    step_start = time.time()
    script, image_prompts = claude_service.generate_reel_script(req.topic, req.language, req.level)
    logger.info("[Step 1/4] Script generated in %.1fs (%d words, %d chars, %d image prompts)",
                time.time() - step_start, len(script.split()), len(script), len(image_prompts))
    logger.info("[Step 1/4] Script output:\n---\n%s\n---", script)

    # Step 2: Generate background images with NVIDIA
    logger.info("[Step 2/4] Generating background images with NVIDIA...")
    step_start = time.time()
    image_paths = []
    # Generate up to 5 images, but no more than number of image prompts
    for i, prompt in enumerate(image_prompts[:5]):
        logger.info("Generating image %d/5...", i + 1)
        img_path = nvidia_service.generate_image(prompt)
        if img_path:
            image_paths.append(img_path)
    logger.info("[Step 2/4] Generated %d images in %.1fs", len(image_paths), time.time() - step_start)

    # Step 3: Generate speech audio with Edge TTS
    logger.info("[Step 3/4] Generating speech audio with Edge TTS...")
    step_start = time.time()
    audio_path = await elevenlabs_service.generate_speech(script, req.language)
    audio_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
    logger.info("[Step 3/4] Audio generated in %.1fs (file: %s, size: %.1f KB)", time.time() - step_start, audio_path, audio_size / 1024)

    # Step 4: Create video with animated captions + audio + background images using FFmpeg
    logger.info("[Step 4/4] Creating video with FFmpeg...")
    step_start = time.time()
    video_path = video_service.create_reel_video(audio_path, script, req.topic, image_paths)
    video_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
    logger.info("[Step 4/4] Video created in %.1fs (file: %s, size: %.1f MB)", time.time() - step_start, video_path, video_size / (1024 * 1024))

    # Build the URL for the frontend to access the video
    video_filename = os.path.basename(video_path)
    video_url = f"/outputs/{video_filename}"

    # Clean up the audio file and images (no longer needed)
    try:
        os.remove(audio_path)
        for img_path in image_paths:
            os.remove(img_path)
        logger.info("Cleaned up temp audio and %d images", len(image_paths))
    except OSError:
        pass

    total_time = time.time() - total_start
    logger.info("COMPLETE in %.1fs — video_url=%s", total_time, video_url)
    logger.info("="*60)

    return {
        "script": script,
        "video_url": video_url,
        "status": "completed",
    }
