# 🎬 LearnCast AI

**Learn anything in 60 seconds.** LearnCast AI is a personalised AI education platform where you type any topic you want to learn and receive a short 30–60 second educational reel: a video with professional voiceover and animated captions that teaches the topic in your chosen language, styled like an engaging TikTok/Reels short for learning.

## ⚡ Tech Stack

- **Frontend:** React (Vite) + Tailwind CSS
- **Backend:** Python FastAPI
- **AI:** Gemini (Google) for script generation, Edge TTS (Microsoft) for voiceover, Flux.1-schnell (NVIDIA) for background visuals
- **Video:** FFmpeg for composing 9:16 vertical reel videos with animated captions and AI-generated background transitions

## 🚀 Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- FFmpeg installed (`brew install ffmpeg` on macOS)

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```
GEMINI_API_KEY=your_key_here
NVIDIA_API_KEY=your_key_here
```

### Frontend

```bash
cd frontend
npm install
```

## ▶️ Run

**Backend** (from the `backend/` directory):

```bash
uvicorn main:app --reload
```

**Frontend** (from the `frontend/` directory):

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

## 🔑 Where to Get API Keys

| Service | URL | Free Tier |
|---------|-----|-----------|
| Google Gemini | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Free tier with generous rate limits |

## 📝 Notes

- **Gemini + NVIDIA + Edge TTS:** Only `GEMINI_API_KEY` and `NVIDIA_API_KEY` are needed. Voice generation uses Edge TTS which is completely free.
- **NVIDIA AI Key:** Get your key at [build.nvidia.com](https://build.nvidia.com/black-forest-labs/flux-1-schnell).
- **Edge TTS:** Microsoft's neural text-to-speech engine — high quality, natural voices, supports 16+ languages, completely free, no limits.
- **Google Gemini Free Tier:** Generous free tier with API access. Get your key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
- **FFmpeg Required:** Must be installed on your system. Install via `brew install ffmpeg` (macOS), `apt install ffmpeg` (Ubuntu), or [ffmpeg.org](https://ffmpeg.org/download.html).
- Videos are generated in **9:16 vertical format** (720×1280) — the standard TikTok/Reels dimension.
- Animated **captions** are overlaid on every reel for the social media feel.
- Video generation typically takes **60–90 seconds** (includes AI script, image generation, voiceover, and video rendering).
