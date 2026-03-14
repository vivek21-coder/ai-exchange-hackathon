import os
import logging
import time
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services import claude_service, elevenlabs_service, video_service

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

    # Step 1: Generate script with Gemini
    logger.info("[Step 1/3] Generating script with Gemini...")
    step_start = time.time()
    script = claude_service.generate_reel_script(req.topic, req.language, req.level)
    logger.info("[Step 1/3] Script generated in %.1fs (%d words, %d chars)", time.time() - step_start, len(script.split()), len(script))
    logger.info("[Step 1/3] Script output:\n---\n%s\n---", script)

    # Step 2: Generate speech audio with Edge TTS
    logger.info("[Step 2/3] Generating speech audio with Edge TTS...")
    step_start = time.time()
    audio_path = await elevenlabs_service.generate_speech(script, req.language)
    audio_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
    logger.info("[Step 2/3] Audio generated in %.1fs (file: %s, size: %.1f KB)", time.time() - step_start, audio_path, audio_size / 1024)

    # Step 3: Create video with animated captions + audio using FFmpeg
    logger.info("[Step 3/3] Creating video with FFmpeg...")
    step_start = time.time()
    video_path = video_service.create_reel_video(audio_path, script, req.topic)
    video_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
    logger.info("[Step 3/3] Video created in %.1fs (file: %s, size: %.1f MB)", time.time() - step_start, video_path, video_size / (1024 * 1024))

    # Build the URL for the frontend to access the video
    video_filename = os.path.basename(video_path)
    video_url = f"/outputs/{video_filename}"

    # Clean up the audio file (no longer needed)
    try:
        os.remove(audio_path)
        logger.info("Cleaned up temp audio file: %s", audio_path)
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
