"""The executors, as the walk receives them — `STEPS` is the one table
`drive/build.py` hands every `Program`; the walk (`walk/surface.py`)
declares its shape and never imports an executor itself.
"""

from physiclaw.conductor.spec.model import (
    AgentNode,
    AskNode,
    DoNode,
    SelectNode,
    TellNode,
)
from physiclaw.conductor.steps.agent import AgentStep
from physiclaw.conductor.steps.ask import AskStep
from physiclaw.conductor.steps.close import CloseStep
from physiclaw.conductor.steps.do import DoStep
from physiclaw.conductor.steps.select import SelectStep
from physiclaw.conductor.steps.tell import TellStep
from physiclaw.conductor.walk.surface import Steps

# `Node` is a closed union; every kind has its executor here.
STEPS = Steps(
    for_node={
        DoNode: DoStep,
        AgentNode: AgentStep,
        AskNode: AskStep,
        TellNode: TellStep,
        SelectNode: SelectStep,
    },
    close=CloseStep,
)
