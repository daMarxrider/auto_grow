# Remote access

The dashboard is protected by HTTP Basic auth (any user name, password from `AUTOGROW_PASSWORD`). Without that variable the server only listens on `127.0.0.1`.

Basic auth is not encrypted on its own, so do not expose the port to the internet directly. Use [Tailscale](https://tailscale.com/kb/1017/install), which encrypts the traffic and needs no port forwarding:

1. On the Pi: `curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up`
2. Install Tailscale on your phone/laptop and log in with the same account.
3. Open `http://<pi-tailscale-name>:8080` and enter the password.

For HTTPS on the tailnet, `sudo tailscale serve --bg 8080` publishes the dashboard at `https://<pi-name>.<tailnet>.ts.net` (enable HTTPS in the Tailscale admin console first).

## Run as a service

See `deploy/autogrow.service` (autostart + restart on crash).

## Camera

`python -m autogrow --camera` takes a photo every 10 min (`--photo-minutes`) with `rpicam-still` and keeps the newest 288 (about two days). Use `--camera-cmd` for a USB webcam, e.g. `--camera-cmd "fswebcam -r 1280x720 --no-banner {out}"`.
