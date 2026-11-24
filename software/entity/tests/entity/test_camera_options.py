from unittest.mock import Mock

import numpy as np
import pytest

from physiclaw.core.hardware import image_controls as hw
from physiclaw.entity import camera

DRIVER = """
  brightness 0x00980900 (int) : min=0 max=255 step=1 default=128 value=128
  power_line_frequency 0x00980918 (menu) : min=0 max=3 default=2 value=2 (60 Hz)
    0: Disabled
    2: 60 Hz
  focus_absolute 0x009a090a (int) : min=0 max=250 step=5 default=0 value=60
  sharpness 0x0098091b (int) : min=0 max=255 step=1 default=128 value=128 flags=inactive
  zoom_absolute 0x009a090d (int) : min=100 max=500 step=1 default=100 value=100
"""


@pytest.fixture
def device(monkeypatch, tmp_path):
    values = {"brightness": 128}
    writes = []

    def driver(index, *args):
        if args[0].startswith("--set-ctrl="):
            _, name, value = args[0].split("=")
            values[name] = int(value)
            writes.append((name, int(value)))
            return ""
        return DRIVER.replace("value=128", f"value={values['brightness']}", 1)

    monkeypatch.setattr(hw, "driver", driver)
    monkeypatch.setattr(hw, "camera_key", lambda _index: "c922")
    monkeypatch.setattr(hw, "preset_path", lambda key: tmp_path / key / "preset.json")
    return values, writes


def body(name="brightness", value=125, previous=128):
    return {"device": "c922", "control": name, "value": value, "previous": previous}


def test_options_follow_driver_and_preserve_calibration_controls(device):
    info = hw.describe(0)
    assert set(info["controls"]) == {"brightness", "power_line_frequency"}
    assert info["controls"]["power_line_frequency"]["choices"] == [0, 2]
    assert info["optics"] == {"focus_absolute": 60}
    assert device[1] == []


@pytest.mark.parametrize(
    "request_body",
    [
        body("focus_absolute"),
        body("zoom_absolute"),
        body("power_line_frequency", 1),
        body(value=256),
        body(value=True),
        body(previous=90),
        body() | {"device": "another"},
    ],
)
def test_rejects_unsupported_or_stale_changes_without_writing(device, request_body):
    with pytest.raises(hw.CameraOptionError):
        hw.apply_option(0, request_body)
    assert device[1] == []


def test_preset_readback_reconnect_and_save_failure(device, monkeypatch):
    values, writes = device
    assert hw.apply_option(0, body())["controls"]["brightness"]["value"] == 125
    assert hw.read_preset("c922") == {"brightness": 125}
    values["brightness"] = 128
    monkeypatch.setattr(hw.sys, "platform", "linux")
    hw.restore_options(0)
    assert writes == [("brightness", 125)] * 2
    monkeypatch.setattr(hw, "write_text_atomic", Mock(side_effect=OSError))
    with pytest.raises(hw.CameraOptionError, match="preset_unavailable"):
        hw.apply_option(0, body(value=130, previous=125))
    assert values["brightness"] == 125
    assert hw.read_preset("c922") == {"brightness": 125}


def test_preview_only_reads_connected_camera(mocker):
    rig = mocker.MagicMock()
    frame = np.zeros((1920, 1080, 3), dtype=np.uint8)
    rig.cam.preview_frame.return_value = frame
    assert camera.preview(rig).startswith(b"\xff\xd8")
    rig.cam.preview_frame.assert_called_once()
    rig.park.assert_not_called()
    rig.connect_camera.assert_not_called()
    rig.cam = None
    with pytest.raises(hw.CameraOptionError, match="camera_offline"):
        camera.preview(rig)
