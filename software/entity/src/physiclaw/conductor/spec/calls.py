"""The model-call vocabulary the parser and the walk share, code-owned.

A playbook never defines a prompt shape or an answer space; it names
steps, and every model call behind a step reads its vocabulary from
here — so the parser's allowlist and the runner's answer space can
never disagree. `ESCALATE` is every call's exit: the model hands the
walk over rather than guessing.
"""

ESCALATE = "escalate"

# The `agent` step's episode vocabulary. `AGENT_DONE` and `ESCALATE`
# are every episode's exits; each grantable tool adds its verbs. One
# map, so the parser's allowlist (`AGENT_TOOLS`), the runner's per-turn
# answer space, and the candidate builder's reserved words
# (`ACT_VERBS`) cannot drift.
AGENT_DONE = "done"

# An agent reply is a TOOL CALL — one envelope for every move:
# `{"reason", "action": <tool name>, "args": {<that tool's arguments>},
# "confidence"}`. The tools are the ones a playbook grants (`tools:`),
# plus the macro run and the two exits; each has its own argument keys,
# spelled once in `TOOL_ARGS`: the parser requires exactly those, and a
# test pins each `TOOL_LEGEND` line to them, so the prompt can never
# describe a tool the code reads differently.
TOOL_TAP = "tap"  # args: label (what the box is), at (the box)

TOOL_SCROLL = "scroll"  # args: direction ("down" | "up")

TOOL_BACK = "back"  # args: none — the OS back edge-swipe

TOOL_RUN = "run_macro"  # args: name (a granted macro)

AGENT_TOOLS = (TOOL_TAP, TOOL_SCROLL, TOOL_BACK)  # what a playbook may grant

# The walk's routing arms behind the scroll and back tools (the swipe
# to send, the edge-swipe) — and parse_task's own `scroll_up` escape.
ACT_SCROLL_DOWN = "scroll_down"  # see content further down (the swipe goes up)

ACT_SCROLL_UP = "scroll_up"  # back toward the top (the swipe goes down)

ACT_BACK = "go_back"

# The scroll tool's direction words and the arm each one swipes by.
SCROLL_ARMS = {"down": ACT_SCROLL_DOWN, "up": ACT_SCROLL_UP}

# Every word an agent call's `action` may be. A recorded call's
# `allowed` mixes these with the granted macro names (kind-tagged,
# `macro:<name>`), and the parser tells them apart by this set.
ACTION_WORDS = frozenset({AGENT_DONE, ESCALATE, TOOL_RUN, *AGENT_TOOLS})

# The reply's fields. parse_task answers a question, so its word is an
# ANSWER; an agent call's is an ACTION with its ARGS beside it. A tap's
# `label` is the macro grammar's word for the same thing — what the box
# IS (`tap: "Paste"` + `at:`), so a model tap and a recorded step share
# one shape on the wire and in the log.
ANSWER = "answer"

ACTION = "action"

ARGS = "args"

LABEL = "label"

AT = "at"

DIRECTION = "direction"

NAME = "name"

# Each tool's argument keys, in the order the legend spells them.
# `done`'s args are the step's declared return fields, so it has no
# fixed keys here.
TOOL_ARGS: dict[str, tuple[str, ...]] = {
    TOOL_TAP: (LABEL, AT),
    TOOL_SCROLL: (DIRECTION,),
    TOOL_BACK: (),
    TOOL_RUN: (NAME,),
    AGENT_DONE: (),
    ESCALATE: (),
}

# What a granted macro or landmark may never be named as. A macro's
# name rides in its own arg (`name`), never in `action`, and a landmark
# is only shown (the model taps its box), so a tool name cannot shadow
# anything — a landmark called `back` is fine. The exits, the macro run
# and the walk's arms stay reserved: a landmark spelled `done` or
# `scroll_up` would read as a lie in the block and the log.
RESERVED_KEYS = frozenset(
    {AGENT_DONE, ESCALATE, TOOL_RUN, ACT_SCROLL_DOWN, ACT_SCROLL_UP, ACT_BACK}
)

# The output contract's own fields — a declared return field may not
# reuse one (it would collide with the envelope around the args).
CONTRACT_FIELDS = frozenset({"reason", ANSWER, ACTION, ARGS, "confidence"})
