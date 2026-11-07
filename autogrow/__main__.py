import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from urllib.parse import parse_qs, urlparse

from .sensors import make_sensor
from .storage import Storage


def collect(sensor, storage, interval):
    while True:
        try:
            storage.add(*sensor.read())
        except Exception as e:  # keep running on transient sensor errors
            print("sensor error:", e)
        time.sleep(interval)


def make_handler(storage):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            u = urlparse(self.path)
            if u.path == "/api/readings":
                secs = int(parse_qs(u.query).get("seconds", ["604800"])[0])
                body, ctype = json.dumps(storage.since(secs)).encode(), "application/json"
            elif u.path == "/":
                body, ctype = files("autogrow").joinpath("dashboard.html").read_bytes(), "text/html"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sensor", choices=["sim", "sht31"], default="sim")
    ap.add_argument("--interval", type=int, default=30, help="seconds between readings")
    ap.add_argument("--db", default="autogrow.db")
    ap.add_argument("--port", type=int, default=8080)
    a = ap.parse_args()
    storage = Storage(a.db)
    threading.Thread(target=collect, args=(make_sensor(a.sensor), storage, a.interval), daemon=True).start()
    print(f"Dashboard on http://0.0.0.0:{a.port}")
    ThreadingHTTPServer(("0.0.0.0", a.port), make_handler(storage)).serve_forever()


main() if __name__ == "__main__" else None
