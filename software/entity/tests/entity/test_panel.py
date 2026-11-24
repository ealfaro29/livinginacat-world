from contextlib import contextmanager
from types import SimpleNamespace

from physiclaw.entity.panel import MKSPublisher, encoded, frame_commands, page_content


def snapshot():
    return {
        "current": {"id": 9, "title": "¿Revisar?!"},
        "action": "peek",
        "queue": [{"title": f"Tarea {i}"} for i in range(1, 8)],
    }


def test_screen_page_is_complete_and_realtime_characters_never_hit_grbl():
    state = snapshot()
    commands = list(frame_commands(4, page_content(state, True, 1)))
    assert commands[0] == "$EP=B,4,1,9,7,1"
    assert bytes.fromhex(commands[1].split(",")[1]).decode() == "¿Revisar?!"
    assert [bytes.fromhex(line.split(",")[1]).decode() for line in commands[3:6]] == [
        "Tarea 4",
        "Tarea 5",
        "Tarea 6",
    ]
    assert commands[-1] == "$EP=E,4"
    assert all(
        len(line) < 256 and not any(ch in line for ch in "?!~\r\n") for line in commands
    )
    assert bytes.fromhex(encoded("é" * 120)).decode().endswith("…")
    assert page_content(state, True, 999)[-1] == ("Tarea 7",)


def test_publisher_uses_owned_transport_and_recovers_after_board_reset():
    sent = []
    board = {"seq": 0}

    def send(cmd, *, diagnostics=None):
        sent.append(cmd)
        if cmd == "$EP":
            diagnostics.append(f"[ENTITY:1,0,{board['seq']},{board['seq']},2,0,40]")
            diagnostics.append("[ENTITY:TOUCH,1,800,1800,400,207,216,0]")
        elif cmd.startswith("$EP=E,"):
            board["seq"] = int(cmd.split(",")[1])

    locked = {"available": True}

    @contextmanager
    def try_locked(timeout):
        assert timeout == 0
        yield locked["available"]

    transport = SimpleNamespace(send=send)
    rig = SimpleNamespace(
        try_locked=try_locked,
        status=lambda: {"ready": True, "arm": True},
        require_arm=lambda: SimpleNamespace(transport=transport),
    )
    publisher = MKSPublisher(SimpleNamespace(snapshot=snapshot), rig)
    publisher.sync()
    assert board["seq"] == 1 and all(i.startswith("$EP") for i in sent)
    sent.clear()
    publisher.sync()
    assert sent == ["$EP"] and publisher.report["rendered"] == 1
    assert publisher.report["touch_sample"]["x"] == 207
    locked["available"] = False
    publisher.sync()
    assert sent == ["$EP"]
    locked["available"] = True
    board["seq"] = 0
    publisher.sync()
    assert board["seq"] == 1 and sent[-1] == "$EP=E,1"
