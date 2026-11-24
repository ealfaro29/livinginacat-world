"""The user channel, loaded, as data: the channel pack (thread
fingerprints, the send/open hands, the boot) and what a walk asks of
it. `load/channel.py` builds one off the disk; the walk and the wake
type against this.
"""

from dataclasses import dataclass

from physiclaw.common.bbox import Bbox
from physiclaw.conductor.spec import reply
from physiclaw.conductor.spec.conventions import CHANNEL_APP, OPEN_MACRO, SEND_MACRO
from physiclaw.conductor.spec.model import Playbook
from physiclaw.conductor.spec.pack import Pack, qualified_macro, qualified_pack
from physiclaw.conductor.spec.pages import PagePrint
from physiclaw.macros.model import Macro


@dataclass(frozen=True)
class Channel:
    """The loaded user-channel infrastructure. `send`/`open` resolve only
    when the macro exists AND is live (enabled, and so is every macro it
    runs) — a missing `send` degrades to hand-over at the ask that needs
    it. `boot` is the boot playbook when it is live (on disk, valid,
    enabled, every hand it names enabled) — else None, the reason
    logged, and the wake is a plain model session; `pack` is what the
    boot builds against; `im` is the IM app the pack automates (its
    folder under `channel/`, which its manifest's `app:` names)."""

    pack: Pack
    im: str
    boot: Playbook | None = None

    @property
    def prints(self) -> tuple[PagePrint, ...]:
        """The thread's page fingerprints — what a channel-facing action
        matches against."""
        return self.pack.prints

    @property
    def macros(self) -> dict[str, Macro]:
        """The pack's hands under their qualified `channel/<name>` keys,
        enabled or not."""
        return qualified_pack(CHANNEL_APP, self.pack)

    @property
    def incoming(self) -> Bbox:
        """Where the user's bubbles sit in this IM (`reply.incoming_box`)."""
        return reply.incoming_box(self.im)

    def _live(self, name: str) -> str | None:
        m = self.pack.macros.get(name)
        return qualified_macro(CHANNEL_APP, name) if m is not None and m.live else None

    @property
    def send(self) -> str | None:
        return self._live(SEND_MACRO)

    @property
    def open(self) -> str | None:
        return self._live(OPEN_MACRO)
