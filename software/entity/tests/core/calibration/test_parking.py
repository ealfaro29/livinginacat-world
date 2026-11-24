import numpy as np
import pytest

from physiclaw.core.calibration.parking import nearest_park, parking_positions
from physiclaw.core.calibration.state import Calibration
from physiclaw.core.orchestration.rig import HardwareRig

# Portrait iPhone, X increases to the right. Bottom is negative work Y.
AFFINE = np.array([[66.0, 0.0, -33.0], [0.0, -142.0, 71.0]])


def test_only_reachable_corners_and_nearest_in_mm():
    parks = parking_positions(AFFINE)
    # A sideways offset only clears the tip. The bridge still spans the phone.
    assert set(parks) == {"top-left"}
    checked = parking_positions(AFFINE, ("top-right", "bottom-right"))
    assert set(checked) == {"top-left", "top-right", "bottom-right"}
    assert nearest_park(checked, (32.0, -65.0)) == checked["bottom-right"]


def test_checked_corners_cannot_enlarge_the_build():
    wide = np.array([[97.0, 0.0, -48.5], [0.0, 142.0, -71.0]])
    with pytest.raises(ValueError, match="travel"):
        parking_positions(wide, ("top-right", "bottom-right"))


def test_parks_rotate_with_the_glass():
    turned = np.array([[0.0, 66.0, -33.0], [142.0, 0.0, -71.0]])
    parks = parking_positions(turned, ("bottom-right",))
    assert nearest_park(parks, (32.0, 70.0)) == parks["bottom-right"]


def test_alternate_park_does_not_rezero_after_interruption(tmp_path, mocker):
    def rig_at(xy):
        r = HardwareRig()
        r._away_marker = tmp_path / "reference-unconfirmed"
        r._arm = mocker.Mock()
        r._arm.position.return_value = xy
        r.calibration = Calibration(
            pct_to_grbl=AFFINE, confirmed_park_corners=("top-right",)
        )
        return r

    first = rig_at((32.0, 65.0))
    first._origin_pinned = True
    first.park()
    xy = parking_positions(AFFINE, ("top-right",))["top-right"]
    first.arm.rapid_to.assert_called_once_with(*xy)
    first.arm.position.return_value = xy
    first.park()
    assert first.arm.rapid_to.call_count == 1  # repeated camera frames keep still
    cold = rig_at(xy)
    assert not cold.restore_park_origin()
    cold.arm.set_work_position.assert_not_called()
    first.park(reference=True)
    assert cold.restore_park_origin()
    cold.arm.set_work_position.assert_called_once_with(
        *parking_positions(AFFINE)["top-left"]
    )


def test_clearances_round_trip_and_reset_on_new_arm_fit():
    r = HardwareRig()
    r.calibration = Calibration.from_dict(
        Calibration(
            pct_to_grbl=AFFINE, confirmed_park_corners=("bottom-right",)
        ).to_dict()
    )
    assert r.calibration.confirmed_park_corners == ("bottom-right",)
    r.install_arm_calibration(AFFINE)
    assert r.calibration.confirmed_park_corners == ()


def test_front_park_leaves_the_full_iphone_clear_after_recalibration(tmp_path, mocker):
    from physiclaw.core.calibration import state

    old = np.array([[64.408, -0.723, -31.842], [-0.995, -140.284, 70.640]])
    new = np.array([[64.316, -0.658, -31.829], [-1.177, -139.831, 70.504]])
    marked = {
        "bottom-left": (-38.248, -104.247),
        "bottom-right": (47.752, -104.247),
        "top-right": (47.752, 87.753),
        "top-left": (-43.248, 87.753),
    }
    prior = Calibration(pct_to_grbl=old, travel_limits=marked, travel_marks=marked)
    mocker.patch.object(state, "BUNDLE_PATH", tmp_path / "bundle.json")
    prior.remember_travel()
    rig = HardwareRig()
    rig._away_marker = tmp_path / "away"
    rig._arm = mocker.Mock()
    rig.install_arm_calibration(new)
    assert rig.calibration.use_measured_travel(Calibration.saved_travel())
    rig.arm.position.return_value = (-38.226, -70.501)
    assert rig.park() == marked["bottom-left"]
    rig.arm.rapid_to.assert_called_once_with(*marked["bottom-left"])
    for name, xy in marked.items():
        rig.arm.position.return_value = (xy[0] * 0.7, xy[1] * 0.7)
        assert rig.park() == marked[name]
    rig.arm.position.return_value = rig.calibration.pct_to_grbl_mm(-0.1, -0.05)
    assert rig.park() == marked["top-left"]
    assert not rig.calibration.precision_verified

    # An automatic fit stays in a known coordinate system through G92.
    assert rig.calibration.use_measured_travel(prior, origin_shift=(0.5, -1.0))
    assert rig.calibration.travel_limits["bottom-left"] == (-38.748, -103.247)
    rig.install_arm_calibration(-new)
    assert not rig.calibration.use_measured_travel(prior)
    assert not rig.calibration.travel_limits


def test_never_pick_a_side_only_clearance_over_the_front_row():
    taught = {
        "bottom-left": (-46.0, -71.0),
        "bottom-right": (45.0, -71.0),
        "top-right": (45.0, 86.0),
        "top-left": (-46.0, 86.0),
    }
    parks = parking_positions(AFFINE, taught=taught)
    assert set(parks) == {"top-left", "top-right"}
