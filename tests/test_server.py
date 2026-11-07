import base64
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from autogrow.__main__ import make_handler
from autogrow.camera import Camera
from autogrow.control import Config, Controller
from autogrow.storage import Storage


class Null:
    def set(self, *a):
        pass


@pytest.fixture
def server(tmp_path):
    st = Storage(str(tmp_path / "t.db"))
    cam = Camera(str(tmp_path / "p"), "touch {out}", keep=2)
    h = make_handler(st, Controller(Config(), Null(), st), cam, "secret")
    srv = ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}", cam
    srv.shutdown()


def get(url, pw=None, data=None):
    req = urllib.request.Request(url, data=data)
    if pw:
        req.add_header("Authorization", "Basic " + base64.b64encode(f"u:{pw}".encode()).decode())
    return urllib.request.urlopen(req)


def test_auth_required(server):
    url, _ = server
    for pw in (None, "wrong"):
        with pytest.raises(urllib.error.HTTPError) as e:
            get(url + "/api/status", pw)
        assert e.value.code == 401
    assert json.load(get(url + "/api/status", "secret"))["override"] == {}


def test_post_requires_auth(server):
    url, _ = server
    with pytest.raises(urllib.error.HTTPError) as e:
        get(url + "/api/override", None, b"{}")
    assert e.value.code == 401


def test_capture_and_traversal(server):
    url, cam = server
    name = get(url + "/api/camera/capture", "secret", b"").read().decode()
    assert name in json.load(get(url + "/api/camera", "secret"))
    assert get(url + "/photos/" + name, "secret").status == 200
    for bad in ("../t.db", "x.jpg", "..%2Ft.db"):
        with pytest.raises(urllib.error.HTTPError) as e:
            get(url + "/photos/" + bad, "secret")
        assert e.value.code == 404
