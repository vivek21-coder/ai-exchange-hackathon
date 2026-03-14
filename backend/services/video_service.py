import os
import re
import uuid
import subprocess
import json
import math
import random
import logging
import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fastapi import HTTPException

logger = logging.getLogger("learncast.video")


# Video dimensions (9:16 vertical reel)
WIDTH = 720
HEIGHT = 1280
FPS = 24

# Colors (RGB tuples for Pillow)
BG_TOP = (8, 8, 30)
BG_BOTTOM = (18, 10, 40)
ACCENT_PURPLE = (124, 58, 237)
ACCENT_CYAN = (6, 182, 212)
ACCENT_PINK = (236, 72, 153)
TEXT_COLOR = (255, 255, 255)
TEXT_SHADOW = (0, 0, 0)
CARD_BG = (17, 17, 24)
CARD_BORDER = (30, 30, 56)

# Particle seeds for floating elements
random.seed(42)
PARTICLES = [
    {
        "x": random.uniform(0.05, 0.95),
        "y": random.uniform(0.05, 0.95),
        "size": random.uniform(2, 6),
        "speed_x": random.uniform(-0.3, 0.3),
        "speed_y": random.uniform(-0.5, -0.1),
        "color": random.choice([ACCENT_PURPLE, ACCENT_CYAN, ACCENT_PINK]),
        "phase": random.uniform(0, 6.28),
    }
    for _ in range(35)
]

# Decorative orbiting dots
ORBIT_DOTS = [
    {"radius": random.uniform(80, 200), "speed": random.uniform(0.3, 0.8),
     "phase": random.uniform(0, 6.28), "size": random.uniform(3, 7),
     "color": random.choice([ACCENT_PURPLE, ACCENT_CYAN])}
    for _ in range(8)
]


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", audio_path,
            ],
            capture_output=True, text=True, timeout=10,
        )
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read audio duration: {e}")


def split_into_sentences(text: str) -> list:
    """Split script into sentences for caption display."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def get_font(size: int, bold: bool = False, hot: bool = False):
    """Get a font, falling back to default if system fonts aren't available."""
    if hot:
        hot_font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", "Anton-Regular.ttf")
        if os.path.exists(hot_font_path):
            try:
                return ImageFont.truetype(hot_font_path, size)
            except Exception:
                pass

    local_font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", "TikTokSans-Bold.ttf")
    if os.path.exists(local_font_path):
        try:
            return ImageFont.truetype(local_font_path, size)
        except Exception:
            pass

    font_names = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSText.ttf",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for font_path in font_names:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def word_wrap_pil(draw, text, font, max_width):
    """Wrap text to fit within max_width pixels, returns list of lines."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > max_width and current_line:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
    return lines


def draw_text_with_outline(draw, xy, text, font, fill, outline_color=(0, 0, 0), outline_width=3):
    """Draw text with a thick outline for TikTok style."""
    x, y = xy
    # Draw outline by drawing the text multiple times with offsets
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    # Draw main text
    draw.text((x, y), text, font=font, fill=fill)


def draw_gradient_bg(img):
    """Draw a vertical gradient background with subtle noise."""
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * ratio)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * ratio)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))


def draw_glow(draw, cx, cy, radius, color, alpha=0.15):
    """Draw a soft radial glow effect."""
    for r in range(radius, 0, -2):
        factor = (r / radius) * alpha
        c = tuple(int(ch * factor) for ch in color)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)


def draw_particles(draw, t):
    """Draw animated floating particles."""
    for p in PARTICLES:
        px = (p["x"] * WIDTH + p["speed_x"] * t * 60 + math.sin(t * 0.5 + p["phase"]) * 30) % WIDTH
        py = (p["y"] * HEIGHT + p["speed_y"] * t * 40) % HEIGHT
        # Pulsing size
        size = p["size"] * (0.7 + 0.3 * math.sin(t * 2 + p["phase"]))
        alpha = 0.3 + 0.2 * math.sin(t * 1.5 + p["phase"])
        c = tuple(int(ch * alpha) for ch in p["color"])
        draw.ellipse([px - size, py - size, px + size, py + size], fill=c)


def draw_orbit_dots(draw, cx, cy, t):
    """Draw orbiting dots around a center point."""
    for dot in ORBIT_DOTS:
        angle = t * dot["speed"] + dot["phase"]
        dx = cx + dot["radius"] * math.cos(angle)
        dy = cy + dot["radius"] * math.sin(angle) * 0.4  # squashed orbit
        s = dot["size"]
        alpha = 0.4 + 0.3 * math.sin(t + dot["phase"])
        c = tuple(int(ch * alpha) for ch in dot["color"])
        draw.ellipse([dx - s, dy - s, dx + s, dy + s], fill=c)


def draw_rounded_rect(draw, bbox, radius, fill, outline=None, outline_width=1):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=outline_width)


def draw_waveform(draw, y_center, t, width_range, color, bar_count=30):
    """Draw an animated audio waveform visualization."""
    bar_width = 4
    gap = (width_range[1] - width_range[0]) / bar_count
    for i in range(bar_count):
        x = width_range[0] + i * gap
        # Animated bar height
        h = 3 + 15 * abs(math.sin(t * 3 + i * 0.4)) * (0.5 + 0.5 * math.sin(t * 2 + i * 0.2))
        alpha = 0.4 + 0.3 * math.sin(t * 2 + i * 0.3)
        c = tuple(int(ch * alpha) for ch in color)
        draw.rectangle([x, y_center - h, x + bar_width, y_center + h], fill=c)


def draw_progress_bar(draw, t, duration):
    """Draw an animated progress bar with gradient effect."""
    progress = t / duration
    bar_y = HEIGHT - 12
    bar_height = 6
    # Background track
    draw.rounded_rectangle(
        [30, bar_y, WIDTH - 30, bar_y + bar_height],
        radius=3, fill=(30, 30, 50)
    )
    # Fill
    fill_width = int((WIDTH - 60) * progress)
    if fill_width > 0:
        # Gradient from purple to cyan
        for x in range(fill_width):
            ratio = x / max(fill_width, 1)
            r = int(ACCENT_PURPLE[0] + (ACCENT_CYAN[0] - ACCENT_PURPLE[0]) * ratio)
            g = int(ACCENT_PURPLE[1] + (ACCENT_CYAN[1] - ACCENT_PURPLE[1]) * ratio)
            b = int(ACCENT_PURPLE[2] + (ACCENT_CYAN[2] - ACCENT_PURPLE[2]) * ratio)
            draw.line([(30 + x, bar_y), (30 + x, bar_y + bar_height)], fill=(r, g, b))
    # Dot at end
    dot_x = 30 + fill_width
    draw.ellipse([dot_x - 5, bar_y - 2, dot_x + 5, bar_y + bar_height + 2], fill=ACCENT_CYAN)


def draw_timer(draw, t, duration, font):
    """Draw a timer showing elapsed/total time."""
    elapsed = int(t)
    total = int(duration)
    timer_text = f"{elapsed // 60}:{elapsed % 60:02d} / {total // 60}:{total % 60:02d}"
    bbox = draw.textbbox((0, 0), timer_text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((WIDTH - tw - 30, HEIGHT - 40), timer_text, font=font, fill=(148, 163, 184, 150))


def render_frame(t, duration, sentences, topic, fonts, sentence_timings, images):
    """Render a single video frame at time t with background images and TikTok-style captions."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_TOP)

    # --- Background Image with Ken Burns / Fade effect ---
    if images:
        # Determine which image to show based on time
        num_images = len(images)
        img_idx = int((t / duration) * num_images)
        img_idx = min(img_idx, num_images - 1)

        try:
            bg_img = images[img_idx]
            # Resize and crop to fill
            iw, ih = bg_img.size
            aspect_target = WIDTH / HEIGHT
            aspect_img = iw / ih

            if aspect_img > aspect_target:
                # Image is wider than needed, crop sides
                new_w = int(ih * aspect_target)
                left = (iw - new_w) // 2
                bg_crop = bg_img.crop((left, 0, left + new_w, ih))
            else:
                # Image is taller than needed, crop top/bottom
                new_h = int(iw / aspect_target)
                top = (ih - new_h) // 2
                bg_crop = bg_img.crop((0, top, iw, top + new_h))

            bg_resized = bg_crop.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

            # Subtle Ken Burns (zoom)
            zoom_factor = 1.0 + 0.1 * ((t % (duration / num_images)) / (duration / num_images))
            zw, zh = int(WIDTH * zoom_factor), int(HEIGHT * zoom_factor)
            bg_zoomed = bg_resized.resize((zw, zh), Image.Resampling.LANCZOS)
            # Center crop zoomed image
            zx = (zw - WIDTH) // 2
            zy = (zh - HEIGHT) // 2
            bg_final = bg_zoomed.crop((zx, zy, zx + WIDTH, zy + HEIGHT))

            # No more black overlay as per user request
            img = bg_final
        except Exception as e:
            logger.error("Failed to render background image: %s", e)
            draw_gradient_bg(img)
    else:
        draw_gradient_bg(img)

    draw = ImageDraw.Draw(img)

    title_font, topic_font, hook_font, caption_font, small_font, timer_font = fonts
    num_sentences = len(sentences)

    # --- Floating particles ---
    # draw_particles(draw, t) # Removed for extra clean look

    # --- Top section: branded header ---
    # Re-adding heading (topic) as per user request
    if topic:
        # Subtle glow behind title
        draw_glow(draw, WIDTH // 2, 80, 150, (0, 0, 0), alpha=0.6)

        # Display topic name at top
        topic_text = topic.upper()
        # Truncate if too long
        if len(topic_text) > 30:
            topic_text = topic_text[:27] + "..."

        t_bbox = draw.textbbox((0, 0), topic_text, font=topic_font)
        tw = t_bbox[2] - t_bbox[0]
        th = t_bbox[3] - t_bbox[1]

        # Draw with thick outline for readability without overlay
        draw_text_with_outline(draw, ((WIDTH - tw) // 2, 60), topic_text, topic_font, (255, 255, 255), (0, 0, 0), outline_width=3)

    # --- Topic section ---
    # Removed as per user request (Learning label, Topic name)

    # --- Sentence counter / progress indicator ---
    current_sentence_idx = 0
    for i, (start, end) in enumerate(sentence_timings):
        if t >= start:
            current_sentence_idx = i
    current_sentence_idx = min(current_sentence_idx, num_sentences - 1)

    # --- Audio waveform visualization ---
    # Removed as per user request

    # --- Render caption text ---
    sentence = sentences[current_sentence_idx]
    s_start, s_end = sentence_timings[current_sentence_idx]
    s_duration = s_end - s_start

    # Word-level highlighting
    words = sentence.split()
    total_words_in_sentence = len(words)
    word_highlight_idx = -1
    if total_words_in_sentence > 0:
        # Estimate word timing within sentence proportionally
        word_idx = int(((t - s_start) / s_duration) * total_words_in_sentence)
        word_highlight_idx = min(word_idx, total_words_in_sentence - 1)

    # Calculate fade (less aggressive for TikTok style)
    fade_in_time = 0.15
    fade_out_time = 0.1
    elapsed = t - s_start
    remaining = s_end - t

    alpha = 1.0
    if elapsed < fade_in_time:
        alpha = elapsed / fade_in_time
    elif remaining < fade_out_time:
        alpha = remaining / fade_out_time
    alpha = max(0.0, min(1.0, alpha))

    # Font for TikTok style
    font = hook_font if current_sentence_idx == 0 else caption_font
    max_text_width = WIDTH - 80

    # Draw caption text with word-level highlighting
    words = sentence.split()
    lines = []
    current_line = []
    current_line_width = 0
    space_width = draw.textbbox((0, 0), " ", font=font)[2]

    # Group words into lines for manual rendering (to allow per-word coloring)
    for i, word in enumerate(words):
        w_bbox = draw.textbbox((0, 0), word, font=font)
        w_width = w_bbox[2] - w_bbox[0]

        if current_line_width + w_width > max_text_width and current_line:
            lines.append(current_line)
            current_line = []
            current_line_width = 0

        current_line.append({"text": word, "index": i, "width": w_width})
        current_line_width += w_width + space_width
    if current_line:
        lines.append(current_line)

    line_height = draw.textbbox((0, 0), "Ay", font=font)[3] + 25
    total_text_height = len(lines) * line_height
    # Lower third for captions
    y_text = (HEIGHT * 0.7) - (total_text_height // 2)

    for line in lines:
        line_total_width = sum(w["width"] for w in line) + space_width * (len(line) - 1)
        x_text = (WIDTH - line_total_width) // 2

        for w_info in line:
            # Highlight current word in YELLOW
            fill_color = (255, 255, 0) if w_info["index"] == word_highlight_idx else (255, 255, 255)
            # Apply alpha for fade
            faded_fill = tuple(int(c * alpha) for c in fill_color)
            faded_outline = tuple(int(c * alpha) for c in (0, 0, 0))

            draw_text_with_outline(draw, (x_text, y_text), w_info["text"], font, faded_fill, faded_outline, outline_width=4)
            x_text += w_info["width"] + space_width
        y_text += line_height

    # Removed labels (Hook, Fact counter) as per user request

    # Removed Progress bar and Timer as per user request

    return img


def create_reel_video(audio_path: str, script: str, topic: str, image_paths: list = None) -> str:
    """Create a 9:16 reel video with rich animated visuals, background images, and captions,
    synced to the audio. Returns the path to the output MP4."""

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"reel_{uuid.uuid4().hex[:12]}.mp4"
    output_path = os.path.join(output_dir, output_filename)

    duration = get_audio_duration(audio_path)
    logger.info("Audio duration: %.1fs", duration)
    sentences = split_into_sentences(script)
    num_sentences = len(sentences)
    logger.info("Split script into %d sentences:", num_sentences)

    # Pre-load images
    loaded_images = []
    if image_paths:
        logger.info("Pre-loading %d background images...", len(image_paths))
        for p in image_paths:
            try:
                if os.path.exists(p):
                    img = Image.open(p).convert("RGB")
                    loaded_images.append(img)
            except Exception as e:
                logger.error("Failed to load image %s: %s", p, e)

    for i, s in enumerate(sentences):
        logger.info("  [%d] %s", i + 1, s)

    if num_sentences == 0:
        raise HTTPException(status_code=500, detail="Script has no sentences to render")

    # Calculate per-sentence timings based on word count for better sync
    word_counts = [len(s.split()) for s in sentences]
    total_words = sum(word_counts)
    # Add small padding at start and end
    padding = 0.3
    usable_duration = duration - padding * 2
    sentence_timings = []
    current_time = padding
    for i, wc in enumerate(word_counts):
        proportion = wc / total_words if total_words > 0 else 1 / num_sentences
        s_dur = usable_duration * proportion
        sentence_timings.append((current_time, current_time + s_dur))
        current_time += s_dur

    # Pre-load fonts
    fonts = (
        get_font(28, bold=True),                # title (unused now)
        get_font(32, bold=True, hot=True),      # topic (heading)
        get_font(72, bold=True, hot=True),      # hook caption (increased size)
        get_font(64, bold=True, hot=True),      # normal caption (increased size)
        get_font(13),                           # small labels
        get_font(14),                           # timer
    )

    logger.info("Sentence timings: %s", [(f"{s:.1f}s-{e:.1f}s") for s, e in sentence_timings])

    total_frames = int(math.ceil(duration * FPS))
    logger.info("Rendering %d frames (%d FPS, %.1fs duration)...", total_frames, FPS, duration)

    # Pipe raw frames directly to FFmpeg via stdin
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "pipe:0",
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path,
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        render_start = time.time()
        for frame_num in range(total_frames):
            t = frame_num / FPS
            img = render_frame(t, duration, sentences, topic, fonts, sentence_timings, loaded_images)
            proc.stdin.write(img.tobytes())
            if frame_num % (FPS * 5) == 0:
                logger.info("  Rendered %.0f/%.0fs (%.0f%%)", t, duration, (frame_num / total_frames) * 100)

        proc.stdin.close()
        logger.info("All frames piped in %.1fs, waiting for FFmpeg to finish encoding...", time.time() - render_start)
        ret = proc.wait(timeout=600)
        stderr = proc.stderr.read()

        if ret != 0:
            err_text = stderr.decode("utf-8", errors="replace")
            error_lines = [
                line for line in err_text.split('\n')
                if line.strip()
                and 'configuration:' not in line
                and 'built with' not in line
                and 'Copyright' not in line
                and 'ffmpeg version' not in line.lower()
                and '--enable' not in line
                and not line.startswith('  ')
            ]
            error_msg = '\n'.join(error_lines[-15:]) if error_lines else err_text[-2000:]
            raise HTTPException(
                status_code=500,
                detail=f"FFmpeg video creation failed: {error_msg}",
            )
        video_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        logger.info("Video saved: %s (%.1f MB)", output_path, video_size / (1024 * 1024))
        return output_path

    except subprocess.TimeoutExpired:
        logger.error("FFmpeg timed out after 600s")
        proc.kill()
        raise HTTPException(status_code=500, detail="Video creation timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Video creation failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Video creation failed: {str(e)}")
