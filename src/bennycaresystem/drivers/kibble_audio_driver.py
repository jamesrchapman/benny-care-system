import subprocess
from pathlib import Path

print("=== Kibble audio driver loaded ===")

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
KIBBLE_SHAKE_PATH = ASSETS_DIR / "kibble_shake.mp3"

MAX_PLAY_SECONDS = 10


def _validate_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"audio file not found: {path}")


def play_kibble_shake() -> bool:
    if not KIBBLE_SHAKE_PATH.exists():
        print(f"[AUDIO ERROR] missing file: {KIBBLE_SHAKE_PATH}")
        return False

    try:
        # --- hardening: ensure volume + routing ---
        subprocess.run(
            ["/usr/bin/amixer", "set", "Master", "80%"],
            check=False,
        )

        subprocess.run(
            ["/usr/bin/amixer", "cset", "numid=3", "1"],
            check=False,
        )

        # --- actual playback ---
        subprocess.run(
            [
                "/usr/bin/mpv",
                "--no-video",
                "--quiet",
                "--ao=alsa",
                "--audio-device=alsa/sysdefault:CARD=Headphones",
                str(KIBBLE_SHAKE_PATH),
            ],
            timeout=MAX_PLAY_SECONDS,
            check=True,
        )

        return True

    except subprocess.TimeoutExpired:
        return False

    except subprocess.CalledProcessError:
        return False