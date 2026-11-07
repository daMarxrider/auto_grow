import argparse
import base64
import hmac
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from urllib.parse import parse_qs, urlparse

from .actuators import GpioActuators, SimActuators
from .camera import Camera, capture_loop
from .control import Config, Controller
from .sensors import make_sensor
from .storage import Storage
from .watering import GpioPump, SeesawSoilSensor, SimPump, SimSoilSensor, WaterConfig, Waterer, watering_loop


def collect(sensor, storage, interval, ctl):
    while True:
        try:
            t, rh = sensor.read()
            storage.add(t, rh)
        except Exception as e:  # keep running on transient sensor errors
            print("sensor error:", e)
            t = rh = None
        ctl.step(t, rh)  # also runs on sensor failure so the failsafe triggers
        time.sleep(interval)


def make_handler(storage, ctl, camera=None, password=None, waterer=None):
    class H(BaseHTTPRequestHandler):
        def authed(self):
            """HTTP Basic auth (any user name). Sends the 401 itself on failure."""
            if password is None:
                return True
            try:
                given = base64.b64decode(self.headers.get("Authorization", "")[6:]).decode().partition(":")[2]
            except ValueError:
                given = ""
            if hmac.compare_digest(given.encode(), password.encode()):
                return True
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="auto_grow"')
            self.end_headers()
            return False

        def do_GET(self):
            if not self.authed():
                return
            u = urlparse(self.path)
            if u.path == "/api/camera" and camera:
                body, ctype = json.dumps(camera.list()[-48:]).encode(), "application/json"
            elif u.path.startswith("/photos/") and camera:
                body, ctype = camera.read(u.path[8:]), "image/jpeg"
                if body is None:
                    self.send_error(404)
                    return
            elif u.path == "/api/water" and waterer:
                body, ctype = json.dumps({
                    "soil": storage.last_soil(),
                    "ml_today": storage.water_ml_since(86400),
                    "max_ml": waterer.cfg.max_ml_per_day,
                }).encode(), "application/json"
            elif u.path == "/api/readings":
                secs = int(parse_qs(u.query).get("seconds", ["604800"])[0])
                body, ctype = json.dumps(storage.since(secs)).encode(), "application/json"
            elif u.path == "/api/status":
                body, ctype = json.dumps({"fan": ctl.last[0], "lamp": ctl.last[1], "override": ctl.override}).encode(), "application/json"
            elif u.path == "/":
                body, ctype = files("autogrow").joinpath("dashboard.html").read_bytes(), "text/html"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if not self.authed():
                return
            if urlparse(self.path).path == "/api/camera/capture" and camera:
                try:
                    name = camera.capture()
                except Exception:
                    self.send_error(500, "capture failed")
                    return
                self.send_response(200)
                self.end_headers()
                self.wfile.write(name.encode())
                return
            if urlparse(self.path).path == "/api/water" and waterer:
                ml = waterer.water("manual")
                self.send_response(200 if ml else 429)  # 429: daily cap reached
                self.end_headers()
                self.wfile.write(json.dumps({"ml": ml}).encode())
                return
            if urlparse(self.path).path != "/api/override":
                self.send_error(404)
                return
            try:
                data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                ov = {k: min(1.0, max(0.0, float(data[k]))) for k in ("fan", "lamp") if data.get(k) is not None}
            except (ValueError, TypeError):
                self.send_error(400)
                return
            ctl.override = ov  # empty dict clears the override
            self.send_response(204)
            self.end_headers()

        def log_message(self, *a):
            pass

    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sensor", choices=["sim", "sht31"], default="sim")
    ap.add_argument("--interval", type=int, default=30, help="seconds between readings")
    ap.add_argument("--db", default="autogrow.db")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--actuators", choices=["sim", "gpio"], default="sim")
    ap.add_argument("--vpd-min", type=float, default=0.8)
    ap.add_argument("--vpd-max", type=float, default=1.2)
    ap.add_argument("--temp-soft-max", type=float, default=28.0)
    ap.add_argument("--temp-hard-max", type=float, default=32.0)
    ap.add_argument("--camera", action="store_true", help="enable the tent camera")
    ap.add_argument("--camera-cmd", default="rpicam-still -n -t 1 -o {out}")
    ap.add_argument("--camera-dir", default="photos")
    ap.add_argument("--photo-minutes", type=int, default=10)
    ap.add_argument("--host", default=None, help="bind address (default: 0.0.0.0 with a password, else 127.0.0.1)")
    ap.add_argument("--watering", choices=["off", "sim", "gpio"], default="off")
    ap.add_argument("--soil-minutes", type=int, default=30)
    ap.add_argument("--dry-below", type=float, default=35.0, help="soil moisture %% that triggers watering")
    ap.add_argument("--shot-seconds", type=float, default=10.0)
    ap.add_argument("--ml-per-second", type=float, default=5.0, help="pump calibration")
    ap.add_argument("--max-ml-per-day", type=float, default=500.0)
    a = ap.parse_args()
    password = os.environ.get("AUTOGROW_PASSWORD") or None
    host = a.host or ("0.0.0.0" if password else "127.0.0.1")
    if password is None and host != "127.0.0.1":
        ap.error("set AUTOGROW_PASSWORD to listen on a non-local address")
    cfg = Config(a.vpd_min, a.vpd_max, a.temp_soft_max, a.temp_hard_max)
    storage = Storage(a.db)
    ctl = Controller(cfg, GpioActuators() if a.actuators == "gpio" else SimActuators(), storage)
    threading.Thread(target=collect, args=(make_sensor(a.sensor), storage, a.interval, ctl), daemon=True).start()
    waterer = None
    if a.watering != "off":
        wc = WaterConfig(a.dry_below, a.shot_seconds, a.ml_per_second, a.max_ml_per_day)
        gpio = a.watering == "gpio"
        waterer = Waterer(wc, GpioPump() if gpio else SimPump(), storage)
        soil = SeesawSoilSensor() if gpio else SimSoilSensor()
        threading.Thread(target=watering_loop, args=(soil, waterer, storage, a.soil_minutes), daemon=True).start()
    camera = Camera(a.camera_dir, a.camera_cmd) if a.camera else None
    if camera:
        threading.Thread(target=capture_loop, args=(camera, a.photo_minutes), daemon=True).start()
    print(f"Dashboard on http://{host}:{a.port}" + ("" if password else " (local only, no AUTOGROW_PASSWORD set)"))
    ThreadingHTTPServer((host, a.port), make_handler(storage, ctl, camera, password, waterer)).serve_forever()


main() if __name__ == "__main__" else None
