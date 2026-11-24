from contextlib import nullcontext
from unittest.mock import Mock

import numpy as np
import pytest

from physiclaw.core.calibration.parking import parking_positions, validate_taught_travel
from physiclaw.core.calibration.state import Calibration
from physiclaw.core.geometry.travel import contains
from physiclaw.core.hardware.arm import StylusArm
from physiclaw.core.orchestration.rig import HardwareRig
from physiclaw.entity.travel import operate

MATRIX = np.array([[66.0, 0.0, -33.0], [0.0, -142.0, 71.0]])
POINTS = {
    "bottom-left": (-45.0, -86.0),
    "bottom-right": (44.0, -85.0),
    "top-right": (44.0, 88.0),
    "top-left": (-46.0, 87.0),
}


def test_stops_use_measured_corners_and_stay_with_the_arm_reference():
    validate_taught_travel(MATRIX, POINTS)
    assert parking_positions(MATRIX, taught=POINTS) == POINTS
    assert not contains(POINTS, (-46.0, -86.0))
    c = Calibration(pct_to_grbl=MATRIX, travel_marks=POINTS, travel_limits=POINTS)
    assert Calibration.from_dict(c.to_dict()).travel_limits == POINTS
    rig = HardwareRig()
    rig.calibration = c
    rig.install_arm_calibration(MATRIX)
    assert not c.travel_limits and not c.travel_marks
    with pytest.raises(ValueError, match="need_four"):
        validate_taught_travel(MATRIX, {"bottom-left": POINTS["bottom-left"]})
    with pytest.raises(ValueError, match="corner_order"):
        validate_taught_travel(MATRIX, POINTS | {"top-left": POINTS["bottom-right"]})
    with pytest.raises(ValueError, match="enclose_glass"):
        validate_taught_travel(MATRIX, POINTS | {"top-right": (20.0, 88.0)})
    with pytest.raises(ValueError, match="travel_span"):
        validate_taught_travel(MATRIX, POINTS | {"bottom-left": (-90.0, -86.0)})


def test_movement_replay_marking_and_activation(monkeypatch):
    cal = Calibration(pct_to_grbl=MATRIX, precision_verified=True)
    rig = Mock(origin_pinned=True, calibration=cal)
    rig.locked.side_effect = lambda **_: nullcontext()
    pos = [0.0, 0.0]
    rig.arm.position.side_effect = lambda **_: tuple(pos)

    def move(x, y):
        pos[:] = [x, y]

    rig.arm.teach_to.side_effect = move
    monkeypatch.setattr(Calibration, "save", lambda self, *paths: None)

    def action(kind, **kw):
        s = operate(rig, None, "run")
        return dict(action=kind, frame=s["frame"], **{"from": s["position"]}, **kw)

    cmd = action("jog", direction="front", mm=1)
    assert operate(rig, cmd, "run")["position"] == (0.0, -1.0)
    with pytest.raises(ValueError, match="position_changed"):
        operate(rig, cmd, "run")
    assert rig.arm.teach_to.call_count == 1
    with pytest.raises(ValueError, match="invalid_step"):
        operate(rig, action("jog", direction="front", mm=25), "run")
    for name, point in POINTS.items():
        pos[:] = point
        operate(rig, action("mark", corner=name), "run")
    assert not cal.travel_limits and cal.travel_marks == POINTS
    cmd = action("apply", marks={k: list(v) for k, v in POINTS.items()})
    operate(rig, cmd, "run")
    assert rig.arm.travel_limits == POINTS
    assert rig.arm.teach_to.call_count == 1
    rig.origin_pinned = False
    with pytest.raises(ValueError, match="not_calibrated"):
        operate(rig, None, "run")


def test_normal_motion_rejects_outside_measured_area_before_serial_or_contact():
    arm = object.__new__(StylusArm)
    arm.travel_limits = POINTS
    arm._send = Mock()
    arm.solenoid = Mock()
    with pytest.raises(ValueError, match="outside_travel"):
        arm.rapid_to(90, 0)
    with pytest.raises(ValueError, match="outside_travel"):
        arm.swipe_to(90, 0)
    arm._send.assert_not_called()
    arm.solenoid.held.assert_not_called()


def test_park_on_applied_limits_during_optical_setup_without_enabling_jogs(
    tmp_path, mocker
):
    rig = HardwareRig()
    rig._away_marker = tmp_path / "away"
    rig._arm = mocker.Mock()
    rig.install_arm_calibration(MATRIX)
    rig.calibration.travel_limits = POINTS
    pos = [0.0, -10.0]
    rig.arm.position.side_effect = lambda **_: tuple(pos)

    def move(x, y):
        pos[:] = [x, y]

    rig.arm.rapid_to.side_effect = move
    state = operate(rig, None, "run")
    assert state["can_teach"] is False
    req = {"frame": state["frame"], "from": state["position"]}
    with pytest.raises(ValueError, match="not_calibrated"):
        operate(rig, req | {"action": "jog", "direction": "front", "mm": 5}, "run")
    with pytest.raises(ValueError, match="no_measured_park"):
        operate(rig, req | {"action": "park", "corner": "unknown"}, "run")
    after = operate(rig, req | {"action": "park", "corner": "bottom-left"}, "run")
    assert after["position"] == POINTS["bottom-left"]
    rig.arm.lift_stylus.assert_called_once_with()
    assert not rig.calibration.precision_verified
