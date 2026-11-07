import re
import shlex
import subprocess
import time
from pathlib import Path

NAME = re.compile(r"^\d{10}\.jpg$")


class Camera:
    """Takes photos with an external command and keeps the newest `keep` of them."""

    def __init__(self, directory="photos", cmd="rpicam-still -n -t 1 -o {out}", keep=288):
        self.dir, self.cmd, self.keep = Path(directory), cmd, keep
        self.dir.mkdir(parents=True, exist_ok=True)

    def capture(self):
        out = self.dir / f"{int(time.time())}.jpg"
        argv = [p.format(out=str(out)) for p in shlex.split(self.cmd)]
        subprocess.run(argv, check=True, timeout=30, capture_output=True)
        for old in self.list()[: -self.keep]:
            (self.dir / old).unlink(missing_ok=True)
        return out.name

    def list(self):
        return sorted(p.name for p in self.dir.iterdir() if NAME.match(p.name))

    def read(self, name):
        """Image bytes for a valid photo name, else None (also blocks path traversal)."""
        if not NAME.match(name) or not (self.dir / name).is_file():
            return None
        return (self.dir / name).read_bytes()


def capture_loop(camera, minutes):
    while True:
        try:
            camera.capture()
        except Exception as e:
            print("camera error:", e)
        time.sleep(minutes * 60)
