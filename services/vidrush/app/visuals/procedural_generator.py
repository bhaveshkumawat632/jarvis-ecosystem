import cv2
import numpy as np
import os
import math
from configs.settings import ASSETS_DIR


# ── Theme palettes keyed by emotion / detected keywords ──────────────
_THEMES = {
    "cyberpunk": {
        "bg_top": (15, 5, 25),       # deep purple-black
        "bg_bot": (45, 10, 50),      # dark magenta
        "particles": [(255, 50, 200), (0, 255, 255), (255, 120, 0), (180, 0, 255)],
        "glow": True,
    },
    "horror": {
        "bg_top": (0, 0, 0),
        "bg_bot": (20, 0, 0),
        "particles": [(80, 0, 0), (180, 30, 30), (255, 60, 0), (50, 50, 50)],
        "glow": False,
    },
    "nature": {
        "bg_top": (10, 25, 10),
        "bg_bot": (5, 50, 20),
        "particles": [(100, 220, 80), (60, 180, 120), (200, 255, 150), (255, 255, 200)],
        "glow": True,
    },
    "excitement": {
        "bg_top": (10, 5, 30),
        "bg_bot": (30, 10, 60),
        "particles": [(255, 200, 0), (255, 100, 0), (255, 255, 100), (200, 50, 255)],
        "glow": True,
    },
    "sadness": {
        "bg_top": (5, 5, 15),
        "bg_bot": (15, 15, 40),
        "particles": [(80, 100, 200), (120, 140, 220), (60, 80, 180), (150, 170, 255)],
        "glow": True,
    },
    "default": {
        "bg_top": (8, 8, 18),
        "bg_bot": (20, 15, 40),
        "particles": [(200, 220, 255), (180, 200, 255), (220, 230, 255), (255, 255, 255)],
        "glow": True,
    },
}

_KEYWORD_MAP = {
    "cyberpunk": "cyberpunk", "neon": "cyberpunk", "futuristic": "cyberpunk",
    "rain": "cyberpunk", "city": "cyberpunk", "alley": "cyberpunk",
    "horror": "horror", "scary": "horror", "dark": "horror",
    "fear": "horror", "terror": "horror", "blood": "horror", "ghost": "horror",
    "nature": "nature", "forest": "nature", "ocean": "nature", "mountain": "nature",
    "sad": "sadness", "sadness": "sadness", "cry": "sadness", "grief": "sadness",
    "excit": "excitement", "fast": "excitement", "energy": "excitement",
    "happy": "excitement", "fun": "excitement",
}


def _pick_theme(topic: str, emotion: str = "neutral") -> dict:
    """Choose a visual theme based on topic keywords and emotion."""
    lower = topic.lower()
    for keyword, theme_name in _KEYWORD_MAP.items():
        if keyword in lower:
            return _THEMES[theme_name]
    # Fall back to emotion
    if emotion in _THEMES:
        return _THEMES[emotion]
    return _THEMES["default"]


def generate_particles_video(
    duration: int = 5,
    fps: int = 24,
    size: tuple = (1080, 1920),
    topic: str = "",
    emotion: str = "neutral",
) -> str:
    """Create a themed particle-flow video using OpenCV.

    The particles, colours, and background gradient are chosen to match the
    *topic* keywords (e.g. "cyberpunk", "horror") or the detected *emotion*.

    Always generates a SHORT clip (max 10 s); the downstream LoopEngine
    extends it to the full audio length.

    Returns:
        Absolute path to the generated .mp4 file.
    """
    duration = max(2, min(int(duration), 10))
    theme = _pick_theme(topic, emotion)

    out_path = os.path.join(ASSETS_DIR, f"particles_{duration}s.mp4")
    os.makedirs(ASSETS_DIR, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, size)
    if not writer.isOpened():
        raise RuntimeError(f"Failed to open VideoWriter for {out_path}")

    num_frames = duration * fps
    w, h = size
    n_particles = 140
    palette = theme["particles"]
    bg_top = np.array(theme["bg_top"], dtype=np.uint8)
    bg_bot = np.array(theme["bg_bot"], dtype=np.uint8)

    # Pre-compute vertical gradient image (avoids per-frame recalculation)
    gradient = np.zeros((h, w, 3), dtype=np.uint8)
    for row in range(h):
        t = row / max(h - 1, 1)
        gradient[row, :] = (bg_top * (1 - t) + bg_bot * t).astype(np.uint8)

    # Persistent particles for smooth drift (instead of random every frame)
    px = np.random.randint(0, w, size=n_particles).astype(float)
    py = np.random.randint(0, h, size=n_particles).astype(float)
    radii = np.random.randint(1, 5, size=n_particles)
    speeds = np.random.uniform(0.5, 3.0, size=n_particles)
    colour_idx = np.random.randint(0, len(palette), size=n_particles)

    print(f"[procedural] Generating {num_frames} frames ({duration}s @ {fps}fps) — theme matched for '{topic[:40]}...'")

    for i in range(num_frames):
        frame = gradient.copy()

        # Drift particles upward
        py -= speeds
        # Wrap particles that go off-screen
        offscreen = py < 0
        py[offscreen] = h + np.random.randint(0, 40, size=offscreen.sum())
        px[offscreen] = np.random.randint(0, w, size=offscreen.sum())

        # Slight horizontal sway
        px += np.sin(py / 60.0 + i * 0.05) * 0.4

        for j in range(n_particles):
            c = palette[colour_idx[j]]
            x_pos, y_pos, r = int(px[j]) % w, int(py[j]) % h, int(radii[j])
            if theme["glow"] and r >= 2:
                # Glow halo
                cv2.circle(frame, (x_pos, y_pos), r * 3, tuple(max(0, v // 4) for v in c), -1)
            cv2.circle(frame, (x_pos, y_pos), r, c, -1)

        writer.write(frame)

        if (i + 1) % fps == 0:
            print(f"[procedural]  ... {i + 1}/{num_frames} frames")

    writer.release()
    print(f"[procedural] Saved particle video → {out_path}")
    return out_path
