import subprocess
import os
from datetime import datetime

WEBCAM_DEVICE = "/dev/video0"
FFMPEG = "/usr/bin/ffmpeg"

def capture_snapshot() -> str:
    """
    Captures a single image from a USB webcam using ffmpeg (V4L2).
    Returns the file path.
    Raises RuntimeError on failure.
    """
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = f"/tmp/snapshot_{ts}.jpg"

    cmd = [
        FFMPEG,
        "-loglevel", "error",      # quiet unless something breaks
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-video_size", "640x480",
        "-i", WEBCAM_DEVICE,
        "-frames:v", "1",
        "-update", "1",
        out_path,
    ]

    subprocess.run(cmd, check=True)

    if not os.path.exists(out_path):
        raise RuntimeError("USB webcam snapshot not created")

    return out_path
