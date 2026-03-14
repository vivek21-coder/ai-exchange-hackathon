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
FPS = 30

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


def get_font(size: int, bold: bool = False):
    """Get a font, falling back to default if system fonts aren't available."""
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


def draw_text_with_shadow(draw, xy, text, font, fill, shadow_color=TEXT_SHADOW, shadow_offset=2):
    """Draw text with a shadow for better readability."""
    x, y = xy
    # Draw shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
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
    """Render a single video frame at time t with rich visual elements and background images."""
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
            # bg_img is a PIL Image object (we'll pre-load them for speed)
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
            
            # Darken for readability
            overlay = Image.new('RGB', (WIDTH, HEIGHT), (0, 0, 0))
            img = Image.blend(bg_final, overlay, 0.6)
        except Exception as e:
            logger.error("Failed to render background image: %s", e)
            draw_gradient_bg(img)
    else:
        draw_gradient_bg(img)

    draw = ImageDraw.Draw(img)

    title_font, topic_font, hook_font, caption_font, small_font, timer_font = fonts
    num_sentences = len(sentences)

    # --- Animated background glow orbs ---
    glow_x1 = WIDTH * 0.3 + math.sin(t * 0.3) * 80
    glow_y1 = HEIGHT * 0.2 + math.cos(t * 0.2) * 60
    draw_glow(draw, glow_x1, glow_y1, 200, ACCENT_PURPLE, 0.08)

    glow_x2 = WIDTH * 0.7 + math.cos(t * 0.25) * 70
    glow_y2 = HEIGHT * 0.7 + math.sin(t * 0.3) * 50
    draw_glow(draw, glow_x2, glow_y2, 180, ACCENT_CYAN, 0.06)

    # Third glow for depth
    glow_x3 = WIDTH * 0.5 + math.sin(t * 0.4) * 100
    glow_y3 = HEIGHT * 0.45 + math.cos(t * 0.35) * 80
    draw_glow(draw, glow_x3, glow_y3, 150, ACCENT_PINK, 0.04)

    # --- Floating particles ---
    draw_particles(draw, t)

    # --- Top section: branded header ---
    # Decorative line
    line_alpha = 0.3 + 0.1 * math.sin(t * 2)
    line_color = tuple(int(c * line_alpha) for c in ACCENT_PURPLE)
    draw.line([(60, 55), (WIDTH - 60, 55)], fill=line_color, width=1)

    # "LearnCast AI" badge
    badge_text = "✦ LearnCast AI"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=small_font)
    badge_w = badge_bbox[2] - badge_bbox[0] + 24
    badge_x = (WIDTH - badge_w) // 2
    draw_rounded_rect(draw, [badge_x, 30, badge_x + badge_w, 52], 11,
                      fill=(124, 58, 237, 30), outline=ACCENT_PURPLE, outline_width=1)
    draw.text((badge_x + 12, 33), badge_text, font=small_font, fill=ACCENT_PURPLE)

    # --- Topic card section ---
    # Orbiting dots around topic area
    draw_orbit_dots(draw, WIDTH // 2, 180, t)

    # Topic label
    topic_label = "LEARNING"
    lb = draw.textbbox((0, 0), topic_label, font=small_font)
    lw = lb[2] - lb[0]
    draw.text(((WIDTH - lw) // 2, 80), topic_label, font=small_font,
              fill=(148, 163, 184))

    # Topic name with glow
    topic_lines = word_wrap_pil(draw, topic, topic_font, WIDTH - 100)
    y_topic = 105
    for line in topic_lines:
        bbox = draw.textbbox((0, 0), line, font=topic_font)
        lw = bbox[2] - bbox[0]
        x = (WIDTH - lw) // 2
        # Subtle glow behind text
        draw.text((x, y_topic), line, font=topic_font, fill=TEXT_COLOR)
        y_topic += bbox[3] - bbox[1] + 8

    # Decorative line below topic
    line2_y = y_topic + 10
    line_w = 100 + 30 * math.sin(t * 1.5)
    line_cx = WIDTH // 2
    gradient_line_start = tuple(int(c * 0.5) for c in ACCENT_PURPLE)
    draw.line([(line_cx - line_w, line2_y), (line_cx + line_w, line2_y)],
              fill=gradient_line_start, width=2)

    # --- Sentence counter / progress indicator ---
    current_sentence_idx = 0
    for i, (start, end) in enumerate(sentence_timings):
        if t >= start:
            current_sentence_idx = i
    current_sentence_idx = min(current_sentence_idx, num_sentences - 1)

    # Draw sentence dots (like a carousel indicator)
    dot_y = line2_y + 25
    total_dot_width = num_sentences * 14 - 6
    dot_start_x = (WIDTH - total_dot_width) // 2
    for i in range(num_sentences):
        dx = dot_start_x + i * 14
        if i == current_sentence_idx:
            draw.rounded_rectangle([dx, dot_y, dx + 20, dot_y + 6], radius=3, fill=ACCENT_CYAN)
        elif i < current_sentence_idx:
            draw.ellipse([dx + 1, dot_y, dx + 7, dot_y + 6], fill=ACCENT_PURPLE)
        else:
            draw.ellipse([dx + 1, dot_y, dx + 7, dot_y + 6], fill=(50, 50, 70))

    # --- Audio waveform visualization ---
    wave_y = HEIGHT - 70
    draw_waveform(draw, wave_y, t, (60, WIDTH - 60), ACCENT_PURPLE, bar_count=40)

    # --- Main caption area ---
    sentence = sentences[current_sentence_idx]
    s_start, s_end = sentence_timings[current_sentence_idx]
    s_duration = s_end - s_start

    # Calculate fade
    fade_in_time = min(0.4, s_duration * 0.15)
    fade_out_time = min(0.3, s_duration * 0.1)
    elapsed = t - s_start
    remaining = s_end - t

    if elapsed < fade_in_time:
        alpha = elapsed / fade_in_time
    elif remaining < fade_out_time:
        alpha = remaining / fade_out_time
    else:
        alpha = 1.0
    alpha = max(0.0, min(1.0, alpha))

    # Slide-up animation for caption entry
    slide_offset = 0
    if elapsed < fade_in_time:
        slide_offset = int(20 * (1 - elapsed / fade_in_time))

    # Choose style for hook (first sentence) vs normal captions
    is_hook = current_sentence_idx == 0
    font = hook_font if is_hook else caption_font
    max_text_width = WIDTH - 100

    # Word wrap
    lines = word_wrap_pil(draw, sentence, font, max_text_width)
    line_height = draw.textbbox((0, 0), "Ay", font=font)[3] + 12
    total_text_height = len(lines) * line_height

    # Caption card background (frosted glass effect)
    card_padding = 24
    card_y_start = HEIGHT // 2 - 30 + slide_offset
    card_height = total_text_height + card_padding * 2
    card_x = 30
    card_w = WIDTH - 60

    # Draw card with semi-transparent background
    card_bg = (17, 17, 30)
    border_color = ACCENT_PURPLE if is_hook else CARD_BORDER
    border_alpha = alpha
    faded_border = tuple(int(c * border_alpha) for c in border_color)
    faded_bg = tuple(int(c * alpha * 0.85) for c in card_bg)
    draw_rounded_rect(draw, [card_x, card_y_start, card_x + card_w, card_y_start + card_height],
                      16, fill=faded_bg, outline=faded_border, outline_width=2)

    # Accent bar on left side of card
    accent_color = ACCENT_PURPLE if is_hook else ACCENT_CYAN
    faded_accent = tuple(int(c * alpha) for c in accent_color)
    draw_rounded_rect(draw, [card_x, card_y_start + 8, card_x + 4, card_y_start + card_height - 8],
                      2, fill=faded_accent)

    # Draw caption text
    color = ACCENT_PURPLE if is_hook else TEXT_COLOR
    faded_color = tuple(int(c * alpha) for c in color)
    faded_shadow = tuple(int(c * alpha) for c in TEXT_SHADOW)

    y_text = card_y_start + card_padding
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        x = (WIDTH - lw) // 2
        draw_text_with_shadow(draw, (x, y_text), line, font, faded_color, faded_shadow)
        y_text += line_height

    # Hook label for first sentence
    if is_hook and alpha > 0.5:
        hook_label = "🔥 HOOK"
        hl_bbox = draw.textbbox((0, 0), hook_label, font=small_font)
        hl_w = hl_bbox[2] - hl_bbox[0] + 16
        hl_x = card_x + card_w - hl_w - 10
        hl_y = card_y_start - 12
        faded_accent_bg = tuple(int(c * alpha * 0.7) for c in ACCENT_PURPLE)
        draw_rounded_rect(draw, [hl_x, hl_y, hl_x + hl_w, hl_y + 22], 11,
                          fill=faded_accent_bg)
        draw.text((hl_x + 8, hl_y + 3), hook_label, font=small_font,
                  fill=tuple(int(255 * alpha) for _ in range(3)))

    # --- Fact counter ---
    if current_sentence_idx > 0:
        fact_text = f"#{current_sentence_idx}/{num_sentences - 1}"
        ft_bbox = draw.textbbox((0, 0), fact_text, font=small_font)
        ft_w = ft_bbox[2] - ft_bbox[0] + 16
        ft_x = card_x + 10
        ft_y = card_y_start - 12
        draw_rounded_rect(draw, [ft_x, ft_y, ft_x + ft_w, ft_y + 22], 11,
                          fill=(30, 30, 56))
        draw.text((ft_x + 8, ft_y + 3), fact_text, font=small_font, fill=ACCENT_CYAN)

    # --- Gradient progress bar ---
    draw_progress_bar(draw, t, duration)

    # --- Timer ---
    draw_timer(draw, t, duration, timer_font)

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
        get_font(28, bold=True),   # title
        get_font(26, bold=True),   # topic
        get_font(38, bold=True),   # hook caption
        get_font(34, bold=True),   # normal caption
        get_font(13),              # small labels
        get_font(14),              # timer
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
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
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
        ret = proc.wait(timeout=180)
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
        logger.error("FFmpeg timed out after 180s")
        proc.kill()
        raise HTTPException(status_code=500, detail="Video creation timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Video creation failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Video creation failed: {str(e)}")
