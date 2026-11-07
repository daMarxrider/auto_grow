import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from urllib.parse import parse_qs, urlparse

from .actuators import GpioActuators, SimActuators
from .control import Config, Controller
from .sensors import make_sensor
from .storage import Storage


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


def make_handler(storage, ctl):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            u = urlparse(self.path)
            if u.path == "/api/readings":
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
    a = ap.parse_args()
    cfg = Config(a.vpd_min, a.vpd_max, a.temp_soft_max, a.temp_hard_max)
    storage = Storage(a.db)
    ctl = Controller(cfg, GpioActuators() if a.actuators == "gpio" else SimActuators(), storage)
    threading.Thread(target=collect, args=(make_sensor(a.sensor), storage, a.interval, ctl), daemon=True).start()
    print(f"Dashboard on http://0.0.0.0:{a.port}")
    ThreadingHTTPServer(("0.0.0.0", a.port), make_handler(storage, ctl)).serve_forever()


main() if __name__ == "__main__" else None
