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
    """
    Plays kibble shake sound through system audio.
    Blocking call. Returns True on success.
    """

    _validate_file(KIBBLE_SHAKE_PATH)

    try:
        # --no-video: audio only
        # --quiet: suppress spam
        subprocess.run(
            [
                "/usr/bin/mpv",
                "--no-video",
                "--quiet",
                "--ao=alsa",
                "--audio-device=alsa/plughw:1,0",
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