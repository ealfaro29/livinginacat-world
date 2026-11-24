"""MCPServer instance construction.

Isolated from `physiclaw.core.server.__init__` so the agent-facing
instructions prompt has a single, focused home. The instance is imported
and wired up (tools, routes, singletons) by `physiclaw.core.server.__init__`.

The `instructions` field is delivered to the client at the MCP initialization
handshake — used by external clients (Claude Desktop, OpenClaw, etc.). The
in-tree agent loads the same file directly as a doctrine slot in
`physiclaw/agent/context/PHYSICLAW.md`, so this file is the single source of truth.
Keep it focused on cross-tool reasoning: mental model, tool-choice
trade-offs, operating loop, coordinate conventions, global safety, and
setup gating. Per-tool mechanics live in `@mcp.tool()` docstrings.

Doctrine `{{token}}`s render here too (`common.doctrine.fill_tokens`,
the same pass the engine's prompt composer runs) — before this, a
token in PHYSICLAW.md reached external clients as literal braces.
Config is process-constant, so rendering once at import is stable.
"""

import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from physiclaw import __version__
from physiclaw.common.doctrine import fill_tokens
from physiclaw.common.text import read_text

_PKG_ROOT = Path(__file__).resolve().parents[2]
_INSTRUCTIONS = fill_tokens(
    "PHYSICLAW.md", read_text(_PKG_ROOT / "agent" / "context" / "PHYSICLAW.md")
)


def build_mcp() -> MCPServer:
    """A fresh, unwired MCPServer instance — `app.build_server()` uses this
    so each assembly gets its own instance (tools/routes registered twice
    on one instance would collide)."""
    if os.environ.get("ENTITY_ON_DEMAND") == "1":
        instructions = (
            "Entity by Sentient operates only on explicit operator requests. "
            "For each new request, enqueue its short title and a stable request_id, "
            "then call entity_start with its id when it is first in line. Use the "
            "phone tools for that task and call entity_finish with the verified outcome. "
            "A status check or reconnect never authorizes starting a waiting task. "
            "Use entity_status for the queue. Do not put credentials in task titles.\n\n"
        )
        return MCPServer(
            "Entity by Sentient",
            instructions=instructions + _INSTRUCTIONS,
            version=__version__,
        )
    return MCPServer("physiclaw", instructions=_INSTRUCTIONS, version=__version__)


mcp = build_mcp()
