import os
import uuid
import logging
import edge_tts

logger = logging.getLogger("learncast.tts")

# Language to Edge TTS voice mapping — high quality, natural voices
LANGUAGE_VOICES = {
    "English": "en-US-AriaNeural",
    "Hindi": "hi-IN-SwaraNeural",
    "Spanish": "es-ES-ElviraNeural",
    "French": "fr-FR-DeniseNeural",
    "German": "de-DE-KatjaNeural",
    "Mandarin Chinese": "zh-CN-XiaoxiaoNeural",
    "Arabic": "ar-SA-ZariyahNeural",
    "Portuguese": "pt-BR-FranciscaNeural",
    "Japanese": "ja-JP-NanamiNeural",
    "Korean": "ko-KR-SunHiNeural",
    "Italian": "it-IT-ElsaNeural",
    "Russian": "ru-RU-SvetlanaNeural",
    "Dutch": "nl-NL-ColetteNeural",
    "Turkish": "tr-TR-EmelNeural",
    "Polish": "pl-PL-AgnieszkaNeural",
    "Swedish": "sv-SE-SofieNeural",
}

DEFAULT_VOICE = "en-US-AriaNeural"


async def generate_speech(script: str, language: str) -> str:
    """Generate speech audio from script text using Edge TTS (free, no API key needed).
    Returns the path to the saved MP3 file."""
    from fastapi import HTTPException

    voice = LANGUAGE_VOICES.get(language, DEFAULT_VOICE)
    logger.info("Using voice: %s (language: %s)", voice, language)
    logger.info("Script to speak: %d chars, %d words", len(script), len(script.split()))

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"audio_{uuid.uuid4().hex[:12]}.mp3"
    filepath = os.path.join(output_dir, filename)

    try:
        logger.info("Starting Edge TTS synthesis (rate: -10%%)...")
        communicate = edge_tts.Communicate(script, voice, rate="-10%")
        await communicate.save(filepath)
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        logger.info("Audio saved: %s (%.1f KB)", filepath, file_size / 1024)
        return filepath
    except Exception as e:
        logger.error("Edge TTS failed: %s", str(e))
        raise HTTPException(
            status_code=502,
            detail=f"Edge TTS failed: {str(e)}",
        )
