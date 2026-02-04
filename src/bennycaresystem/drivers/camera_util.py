import subprocess
import tempfile
import os
from datetime import datetime

def capture_snapshot() -> str:
    """
    Captures an image using libcamera and returns the file path.
    Raises on failure.
    """
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = f"/tmp/snapshot_{ts}.jpg"

    cmd = [
        "libcamera-still",
        "-n",              # no preview
        "-t", "1",         # minimal capture time
        "-o", out_path
    ]

    subprocess.run(cmd, check=True)

    if not os.path.exists(out_path):
        raise RuntimeError("snapshot not created")

    return out_path
