"""Forward authenticated operator requests to the fixed Entity services on this Pi."""

import hmac
import http.client
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


CORE_READ = {
    "/entity/", "/entity/state", "/entity/display/state", "/entity/travel",
    "/entity/api/tasks", "/entity/api/travel", "/entity/api/camera/options", "/entity/api/camera/preview",
    "/entity/sentient.svg", "/entity/space-grotesk.ttf",
    "/setup-hardware", "/api/status", "/api/bridge/qr",
    "/assets/qrcode-1.4.4.min.js",
}
CORE_WRITE = {
    "/api/setup/begin", "/api/connect-arm", "/api/connect-camera",
    "/api/disconnect-camera", "/api/ready", "/api/phone/home", "/api/bridge/switch",
    "/api/calibrate/viewport-shift", "/api/calibrate/arm", "/api/calibrate/camera",
    "/api/calibrate/camera-mapping", "/api/calibrate/validate",
    "/api/calibrate/parking-corners", "/api/calibrate/trace-edge",
    "/api/calibrate/assistive-touch/show", "/api/calibrate/assistive-touch/verify",
    "/entity/api/tasks", "/entity/api/travel", "/entity/api/camera/options",
}
PHONE_READ = {"/iphone", "/api/bridge/state", "/api/bridge/clipboard"}
PHONE_WRITE = {"/api/bridge/tapped", "/api/bridge/screen-dimension", "/api/bridge/touch", "/api/bridge/screenshot"}
PULSE_READ = {
    "/control", "/control/state", "/control.js", "/pulse.css", "/sentient.svg",
    "/space-grotesk.ttf", "/jugar", "/pulse.js",
}
PULSE_WRITE = {"/control/start", "/control/stop", "/api/phone"}
MAX_BODY = 16 * 1024
MAX_SCREENSHOT = 10 * 1024 * 1024
MAX_RESPONSE = 4 * 1024 * 1024


def target(path, method):
    if method == "GET":
        if path in CORE_READ or re.fullmatch(r"/api/camera-preview/[0-9]{1,2}", path):
            return 8048
        if path in PHONE_READ:
            return 8049
        if path in PULSE_READ:
            return 8050
    if method == "POST":
        if path in CORE_WRITE:
            return 8048
        if path in PHONE_WRITE:
            return 8049
        if path in PULSE_WRITE:
            return 8050
    return None


class OperatorHandler(BaseHTTPRequestHandler):
    server_version = "Entity"

    def respond(self, status, body=b"", content_type="text/plain; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def handle_operator(self):
        key = self.headers.get("X-Entity-Relay", "").encode()
        if not key or not hmac.compare_digest(key, self.server.relay_key):
            return self.respond(403)
        try:
            url = urlsplit(self.path)
        except ValueError:
            return self.respond(400)
        if url.scheme or url.netloc or url.fragment or not self.path.startswith("/"):
            return self.respond(400)
        camera_operation = (self.command, url.path) in {
            ("GET", "/operator/camera"), ("POST", "/operator/connect-camera"),
        }
        port = 8048 if camera_operation else target(url.path, self.command)
        if port is None:
            return self.respond(404)
        try:
            count = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.respond(400)
        screenshot = self.command == "POST" and url.path == "/api/bridge/screenshot"
        limit = MAX_SCREENSHOT if screenshot else MAX_BODY
        if self.headers.get("Transfer-Encoding") or not 0 <= count <= limit:
            return self.respond(413)
        body = self.rfile.read(count) if count else None
        upstream_path = self.path
        if url.path == "/iphone":
            upstream_path = "/bridge" + ("?" + url.query if url.query else "")
        if camera_operation:
            devices = {p.resolve().name for p in Path("/dev/v4l/by-id").glob("*-video-index0") if p.exists()}
            if len(devices) != 1 or not re.fullmatch(r"video[0-9]{1,2}", next(iter(devices), "")):
                return self.respond(409, b'{"error":"select_camera"}', "application/json")
            index = int(devices.pop().removeprefix("video"))
            if self.command == "GET":
                upstream_path = f"/api/camera-preview/{index}"
            else:
                upstream_path = "/api/connect-camera"
                body = json.dumps({"index": index}).encode()
        # Entity's loopback-only directors receive requests as a local client.
        # Neither the browser's cookies nor forwarding headers enter the rig.
        headers = {"Host": f"127.0.0.1:{port}", "Accept-Encoding": "identity"}
        if self.command == "POST":
            headers["Content-Type"] = self.headers.get("Content-Type", "application/octet-stream") if screenshot else "application/json"
            headers["Origin"] = f"http://127.0.0.1:{port}"
            if url.path in {"/control/start", "/control/stop"}:
                headers["X-Pulse-Control"] = "1"
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=90)
        try:
            conn.request(self.command, upstream_path, body, headers)
            result = conn.getresponse()
            payload = result.read(MAX_RESPONSE + 1)
            if len(payload) > MAX_RESPONSE:
                return self.respond(502)
            return self.respond(result.status, payload, result.getheader("Content-Type") or "application/octet-stream")
        except (OSError, http.client.HTTPException):
            return self.respond(503, b'{"error":"device_offline"}', "application/json")
        finally:
            conn.close()

    do_GET = do_POST = handle_operator

    def log_message(self, *args):
        # Camera requests and time-sensitive control URLs are private.
        pass


if __name__ == "__main__":
    with ThreadingHTTPServer(("127.0.0.1", 8052), OperatorHandler) as server:
        server.relay_key = (Path(os.environ["CREDENTIALS_DIRECTORY"]) / "relay").read_bytes().strip()
        if len(server.relay_key) < 32:
            raise SystemExit("Missing Entity relay credential")
        server.serve_forever()
