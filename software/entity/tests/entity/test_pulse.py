import time
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock

import cv2
import httpx
import numpy as np
import pytest

from physiclaw.entity.pulse import Pulse, build_game
from physiclaw.entity.pulse_hardware import RoundEnded, play_physical, target_center


def board(x=200, y=290, second=False, ring=True):
    frame = np.full((760, 390, 3), (22, 29, 23), np.uint8)
    for px, py in [(x, y), (85, 510)] if second else [(x, y)]:
        if ring:
            cv2.circle(frame, (px, py), 33, (0, 251, 197), 3)
        cv2.circle(frame, (px, py), 18, (52, 103, 255), -1)
    return frame


def test_camera_target_requires_one_disc_with_ring():
    assert target_center(board()) == pytest.approx((200 / 390, 290 / 760), abs=0.002)
    assert target_center(board(second=True)) is None
    assert target_center(board(ring=False)) is None


@pytest.mark.asyncio
async def test_lan_game_cannot_command_motion_and_get_never_starts_it():
    app = build_game("http://phone/jugar")
    for peer, host, status in [
        ("192.168.1.5", "localhost", 403),
        ("127.0.0.1", "untrusted.invalid", 403),
        ("127.0.0.1", "localhost", 405),
    ]:
        transport = httpx.ASGITransport(app=app, client=(peer, 4321))
        async with httpx.AsyncClient(
            transport=transport, base_url="http://" + host
        ) as client:
            assert (await client.get("/jugar")).status_code == 200
            assert (await client.get("/control/start")).status_code == status
            assert (
                await client.post(
                    "/control/start",
                    headers={
                        "origin": "http://another.invalid",
                        "x-pulse-control": "1",
                    },
                )
            ).status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("register_hits", [True, False])
async def test_round_only_counts_hits_reported_by_the_phone(register_hits):
    game = Pulse("http://phone/jugar")
    game.screen_id, game.run_id = "phone", "round"
    screen = {
        "visible": True,
        "lang": "es",
        "round": "round",
        "mode": "entity",
        "phase": "playing",
        "hits": 0,
        "accepting": True,
    }
    game.screens["phone"] = time.monotonic(), screen
    actions = []

    class Client:
        async def call_tool(self, name, arg):
            actions.append((name, arg))
            if name == "entity_status":
                return SimpleNamespace(
                    is_error=False,
                    structured_content={
                        "hardware": {"ready": True},
                        "current": None,
                        "queue": [],
                    },
                )
            if name == "entity_enqueue":
                return SimpleNamespace(is_error=False, structured_content={"id": 7})
            if name == "entity_play_pulse":
                assert arg["task_id"] == 7 and arg["round_id"] == game.run_id
                if register_hits:
                    screen.update(hits=5, phase="won")
                return SimpleNamespace(
                    is_error=False, structured_content={"reason": "done"}
                )
            return SimpleNamespace(is_error=False)

    async def sample(predicate, seconds, failure):
        if not predicate(screen):
            raise RoundEnded(failure)
        return screen

    game.wait_screen = sample
    if register_hits:
        await game.play(Client())
    else:
        with pytest.raises(RoundEnded, match="miss"):
            await game.play(Client())
    assert sum(name == "entity_play_pulse" for name, _ in actions) == 1
    assert game.hits == (5 if register_hits else 0)
    assert actions[-1] == (
        "entity_finish",
        {"task_id": 7, "outcome": "done" if register_hits else "failed"},
    )


def test_camera_accepts_pale_ring_but_rejects_an_unringed_warm_disc():
    frame = board(ring=False)
    cv2.circle(frame, (200, 290), 33, (245, 247, 250), 3)
    assert target_center(frame) == pytest.approx((200 / 390, 290 / 760), abs=0.002)
    assert target_center(board(ring=False)) is None


@pytest.mark.parametrize("drop_first", [False, True])
def test_fast_round_moves_to_five_visible_targets_and_requires_real_ack(
    monkeypatch, drop_first
):
    from physiclaw.entity import pulse_hardware as hw

    points = [(0.25, 0.27), (0.72, 0.27), (0.50, 0.48), (0.26, 0.64), (0.72, 0.64)]
    phone = {"phase": "playing", "hits": 0, "misses": 0, "accepting": True}
    rig = Mock(ready=True, origin_pinned=True)
    rig.calibration.precision_verified = True
    rig.engaged.return_value = nullcontext()
    rig.assistive_touch.overlaps_at.return_value = False
    arm = rig.require_arm()

    def tap(duration):
        assert duration == hw.CAL_STRIKE_DURATION
        if drop_first and arm.tap.call_count == 1:
            return
        phone["hits"] += 1
        if phone["hits"] == 5:
            phone["phase"] = "won"

    arm.tap.side_effect = tap
    monkeypatch.setattr(hw, "screen_target", lambda rig: points[phone["hits"]])
    started = hw.time.monotonic()
    ticks = iter(started + i * 0.3 for i in range(1000))
    monkeypatch.setattr(
        hw, "time", SimpleNamespace(monotonic=lambda: next(ticks), sleep=lambda _: None)
    )
    assert play_physical(rig, lambda: phone.copy()) == {
        "reason": "done",
        "taps": 5 + drop_first,
    }
    assert [c.args[0] for c in rig.move_to_bbox_center.call_args_list] == [
        [x, y, x, y] for x, y in points
    ]
    rig.park.assert_not_called()


def test_fast_round_aborts_on_stop_before_contact(monkeypatch):
    from physiclaw.entity import pulse_hardware as hw

    rig = Mock(ready=True, origin_pinned=True)
    rig.engaged.return_value = nullcontext()
    rig.assistive_touch.overlaps_at.return_value = False
    monkeypatch.setattr(hw, "screen_target", lambda rig: (0.5, 0.5))
    state = {"phase": "playing", "hits": 0, "misses": 0, "accepting": True}
    read = Mock(side_effect=[state, state, state, RoundEnded("stopped")])
    with pytest.raises(RoundEnded, match="stopped"):
        play_physical(rig, read)
    rig.require_arm().tap.assert_not_called()
