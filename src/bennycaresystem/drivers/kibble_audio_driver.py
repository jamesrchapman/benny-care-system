from __future__ import annotations

import subprocess
from enum import Enum
from pathlib import Path
from threading import Lock


print("=== Audio driver loaded ===")

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

MAX_PLAY_SECONDS = 60
MASTER_VOLUME = "80%"
AUDIO_ROUTE_NUMID = "numid=3"
AUDIO_ROUTE_VALUE = "1"
AUDIO_DEVICE = "alsa/sysdefault:CARD=Headphones"

# Invariant:
# Only one audio file should be pushed through mpv at a time.
_PLAYBACK_LOCK = Lock()


class AudioCue(str, Enum):
    KIBBLE_SHAKE = "kibble_shake"
    EMERGENCY_WAKEUP = "emergency_wakeup"
    BENNY_LETS_EAT = "benny_lets_eat"


AUDIO_PATHS: dict[AudioCue, Path] = {
    AudioCue.KIBBLE_SHAKE: ASSETS_DIR / "kibble_shake.mp3",
    AudioCue.EMERGENCY_WAKEUP: ASSETS_DIR / "emergency_wakeup.mp3",
    AudioCue.BENNY_LETS_EAT: ASSETS_DIR / "benny_lets_eat.mp3",
}


COMMAND_TO_CUE: dict[str, AudioCue] = {
    "audio_kibble_shake": AudioCue.KIBBLE_SHAKE,
    "audio_emergency_wakeup": AudioCue.EMERGENCY_WAKEUP,
    "audio_benny_lets_eat": AudioCue.BENNY_LETS_EAT,
}


def _validate_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"audio file not found: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"audio path is not a file: {path}")


def _prepare_audio_output() -> None:
    # Best-effort hardening. These should not kill playback if they fail.
    subprocess.run(
        ["/usr/bin/amixer", "set", "Master", MASTER_VOLUME],
        check=False,
    )
    subprocess.run(
        ["/usr/bin/amixer", "cset", AUDIO_ROUTE_NUMID, AUDIO_ROUTE_VALUE],
        check=False,
    )


def _play_file(path: Path) -> bool:
    _validate_file(path)

    with _PLAYBACK_LOCK:
        _prepare_audio_output()

        subprocess.run(
            [
                "/usr/bin/mpv",
                "--no-video",
                "--quiet",
                "--ao=alsa",
                f"--audio-device={AUDIO_DEVICE}",
                str(path),
            ],
            timeout=MAX_PLAY_SECONDS,
            check=True,
        )

    return True


def play_audio(cue: AudioCue) -> bool:
    path = AUDIO_PATHS[cue]

    try:
        return _play_file(path)

    except FileNotFoundError as exc:
        print(f"[AUDIO ERROR] {exc}")
        return False

    except subprocess.TimeoutExpired:
        print(f"[AUDIO ERROR] playback timed out for cue={cue.value}")
        return False

    except subprocess.CalledProcessError as exc:
        print(
            f"[AUDIO ERROR] mpv exited non-zero for cue={cue.value}, "
            f"returncode={exc.returncode}"
        )
        return False

    except Exception as exc:
        print(f"[AUDIO ERROR] unexpected failure for cue={cue.value}: {exc}")
        return False


def play_kibble_shake() -> bool:
    return play_audio(AudioCue.KIBBLE_SHAKE)


def play_emergency_wakeup() -> bool:
    return play_audio(AudioCue.EMERGENCY_WAKEUP)


def play_benny_lets_eat() -> bool:
    return play_audio(AudioCue.BENNY_LETS_EAT)


def run_audio_command(command_name: str) -> bool | None:
    """
    Returns:
        True/False if command_name is a known audio command.
        None if command_name is not an audio command.
    """
    cue = COMMAND_TO_CUE.get(command_name)
    if cue is None:
        return None

    return play_audio(cue)