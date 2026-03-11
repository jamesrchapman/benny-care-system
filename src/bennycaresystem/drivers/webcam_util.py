import subprocess
import os
from datetime import datetime
import uuid
import time
import inspect

WEBCAM_DEVICE = "/dev/video0"
FFMPEG = "/usr/bin/ffmpeg"

def capture_snapshot() -> str:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = f"/tmp/snapshot_{ts}_{uuid.uuid4().hex}.jpg"
    print("webcam_util file:", inspect.getfile(capture_snapshot))

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

    # retry ffmpeg if the camera is temporarily busy
    for attempt in range(5):

        result = subprocess.run(cmd, capture_output=True)

        # give filesystem a moment
        for _ in range(10):
            if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                return out_path
            time.sleep(0.05)

        stderr = result.stderr.decode(errors="ignore")

        if "Device or resource busy" in stderr:
            time.sleep(0.25)
            continue

        break

    print(
        "snapshot failure:",
        result.returncode,
        stderr[:200]
    )

    raise RuntimeError("USB webcam snapshot not created")