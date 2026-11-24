"""Operator image controls for the connected Linux camera. Never start a stream here."""

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from physiclaw.common import paths
from physiclaw.common.text import write_text_atomic

log = logging.getLogger(__name__)
EDITABLE = ("brightness", "contrast", "saturation", "sharpness", "power_line_frequency")
OPTICS = (
    "focus_absolute",
    "focus_automatic_continuous",
    "exposure_time_absolute",
    "auto_exposure",
)
CONTROL = re.compile(r"^\s*(\w+)\s+0x[0-9a-f]+\s+\((\w+)\)\s*:\s*(.*)$")


class CameraOptionError(Exception):
    def __init__(self, code: str, status: int = 409):
        super().__init__(code)
        self.code = code
        self.status = status


def driver(index: int, *args: str) -> str:
    if sys.platform != "linux" or type(index) is not int or index < 0:
        raise CameraOptionError("controls_unavailable")
    try:
        return subprocess.check_output(
            ["v4l2-ctl", "-d", f"/dev/video{index}", *args],
            env={**os.environ, "LC_ALL": "C"},
            stderr=subprocess.DEVNULL,
            timeout=3,
            text=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CameraOptionError("controls_unavailable") from exc


def parse_controls(output: str) -> tuple[dict, dict]:
    controls, optics = {}, {}
    menu = None
    for line in output.splitlines():
        match = CONTROL.match(line)
        if not match:
            item = re.fullmatch(r"\s+(\d+):\s+.*", line)
            if menu is not None and item:
                # These are the standard off / 50 Hz / 60 Hz / automatic menu IDs.
                value = int(item[1])
                if value in range(4):
                    menu.append(value)
            continue
        name, kind, fields = match.groups()
        menu = None
        values = {k: int(v) for k, v in re.findall(r"(\w+)=(-?\d+)", fields)}
        if name in OPTICS and "value" in values:
            optics[name] = values["value"]
        if name not in EDITABLE or any(
            flag in fields for flag in ("inactive", "read-only", "disabled")
        ):
            continue
        if not {"min", "max", "value"} <= values.keys():
            continue
        if name == "power_line_frequency" and kind == "menu":
            menu = []
            controls[name] = {"value": values["value"], "choices": menu}
        elif kind == "int" and values.get("step", 0) > 0:
            controls[name] = {k: values[k] for k in ("value", "min", "max", "step")}
    return {k: v for k, v in controls.items() if v.get("choices", [1])}, optics


def camera_key(index: int) -> str | None:
    device = Path(f"/dev/video{index}")
    for link in sorted(Path("/dev/v4l/by-id").glob("*-video-index0")):
        if link.resolve() == device:
            return hashlib.sha256(link.name.encode()).hexdigest()[:24]
    return None


def preset_path(key: str) -> Path:
    return paths.HOME / "entity" / "camera" / f"{key}.json"


def read_preset(key: str) -> dict:
    try:
        values = json.loads(preset_path(key).read_text())
        if isinstance(values, dict):
            return values
        raise ValueError
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        raise CameraOptionError("preset_unavailable") from exc


def describe(index: int) -> dict:
    output = driver(index, "--list-ctrls-menus", "--get-fmt-video")
    controls, optics = parse_controls(output)
    size = re.search(r"Width/Height\s*:\s*(\d+)/(\d+)", output)
    try:
        name = Path(f"/sys/class/video4linux/video{index}/name").read_text().strip()
    except OSError:
        name = None
    return {
        "model": name,
        "size": [int(x) for x in size.groups()] if size else None,
        "device": camera_key(index),
        "controls": controls,
        "optics": optics,
    }


def accepts(control: dict | None, value: int) -> bool:
    if not control or type(value) is not int:
        return False
    if "choices" in control:
        return value in control["choices"]
    return (
        control["min"] <= value <= control["max"]
        and (value - control["min"]) % control["step"] == 0
    )


def apply_option(index: int, request: dict) -> dict:
    state = describe(index)
    key = state["device"]
    name, value, previous = (request.get(k) for k in ("control", "value", "previous"))
    if not isinstance(name, str) or name not in EDITABLE or type(previous) is not int:
        raise CameraOptionError("invalid_control", 400)
    control = state["controls"].get(name)
    if not accepts(control, value):
        raise CameraOptionError("invalid_control", 400)
    if request.get("device") != key or control["value"] not in (previous, value):
        raise CameraOptionError("settings_changed")
    saved = read_preset(key) if key else {}
    old = control["value"]
    if old != value:
        driver(index, f"--set-ctrl={name}={value}")
    try:
        state = describe(index)
        if (
            state["device"] != key
            or state["controls"].get(name, {}).get("value") != value
        ):
            raise CameraOptionError("setting_rejected")
        if key and saved.get(name) != value:
            path = preset_path(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            write_text_atomic(path, json.dumps({**saved, name: value}))
    except (CameraOptionError, OSError) as exc:
        if old != value and camera_key(index) == key:
            driver(index, f"--set-ctrl={name}={old}")
        if isinstance(exc, OSError):
            raise CameraOptionError("preset_unavailable") from exc
        raise
    return state


def restore_options(index: int) -> None:
    """Restore only operator-saved image settings for this physical camera."""
    if sys.platform != "linux" or type(index) is not int or index < 0:
        return
    try:
        key = camera_key(index)
        saved = read_preset(key) if key else {}
        if not saved:
            return
        controls = describe(index)["controls"]
        for name, value in saved.items():
            control = controls.get(name)
            if (
                name in EDITABLE
                and accepts(control, value)
                and control["value"] != value
            ):
                driver(index, f"--set-ctrl={name}={value}")
    except (OSError, CameraOptionError):
        log.warning("Could not restore saved camera image settings", exc_info=True)
