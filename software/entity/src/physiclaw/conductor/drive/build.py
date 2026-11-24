"""Building a walk — the one `Program` constructor call.

`build_program` is how every door assembles a walk — the wake's
suspension and boot, the CLI rehearsal, the stepping tool, the offline
replay, and the tests — so a program is whole at construction (channel,
OS prints, any restored projection) and never patched up afterwards.
"""

from physiclaw.conductor.load import prints
from physiclaw.conductor.spec.channel import Channel
from physiclaw.conductor.spec.model import Playbook
from physiclaw.conductor.spec.pack import Pack, qualified_inline, qualified_pack
from physiclaw.conductor.steps.table import STEPS
from physiclaw.conductor.walk.program import Program
from physiclaw.conductor.walk.surface import Activator
from physiclaw.conductor.walk.thread import Thread
from physiclaw.contract.plugin import EventSink


def build_program(
    spec: Playbook,
    pack_: Pack,
    values: dict[str, str],
    channel: Channel | None,
    *,
    suspended: dict | None = None,
    position: dict | None = None,
    dry: bool = False,
    activation: Activator | None = None,
    events: "EventSink | None" = None,
    thread: "Thread | None" = None,
) -> "Program":
    """The one Program constructor call — the boot's activation, a
    resumed suspension, the CLI rehearsal, and the offline replay all
    come through here, so a program is whole at construction (channel
    and any suspended state included) and never patched up afterwards.
    `dry` (the replay, the boot) runs the walk without writing any
    record; `position` is a stepping tool's checkpoint — the projection
    overlaid without a wake-suspension's one-time unlock (`Program`);
    `activation` is the boot's menu of enabled playbooks
    (`activation.activation_for`), which every door passes when the
    route activates; `events` is the session's event stream, so the
    walk's terminal moment lands in events.jsonl (None outside a wake)."""
    return Program(
        steps=STEPS,
        spec=spec,
        values=values,
        pack_macros=qualified_pack(spec.app, pack_) | qualified_inline(spec.app, spec),
        prints=[*pack_.prints, *prints.os_prints()],
        channel=channel,
        suspended=suspended,
        position=position,
        landmarks=pack_.landmarks,
        dry=dry,
        activation=activation,
        events=events,
        thread=thread,
    )
