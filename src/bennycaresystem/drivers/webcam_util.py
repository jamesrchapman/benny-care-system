import subprocess
import os
from datetime import datetime
import uuid
import time

WEBCAM_DEVICE = "/dev/video0"
FFMPEG = "/usr/bin/ffmpeg"

def capture_snapshot() -> str:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = f"/tmp/snapshot_{ts}_{uuid.uuid4().hex}.jpg"

    cmd = [
        FFMPEG,
        "-loglevel", "error",
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-video_size", "640x480",
        "-i", WEBCAM_DEVICE,
        "-frames:v", "1",
        "-update", "1",
        out_path,
    ]

    result = subprocess.run(cmd, capture_output=True)

    if result.returncode != 0:
        print(
            "ffmpeg warning:",
            result.returncode,
            result.stderr.decode(errors="ignore")[:200]
        )

    for _ in range(10):
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return out_path
        time.sleep(0.05)

    raise RuntimeError("USB webcam snapshot not created")