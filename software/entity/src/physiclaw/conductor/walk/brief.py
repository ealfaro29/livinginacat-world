"""The handover brief — the conductor's distilled report to the model.

A walk that stops mints ONE last synthesized ``[note, peek]`` turn
whose note carries these renderings, then answers None forever. The
note summary is exactly what compaction preserves, so the brief
outlives the turns it summarizes and the model never resumes blind;
the peek hands it the fresh view it would have had to take anyway (and
on a dead phone its error result is itself the evidence).

Pure text: the walk passes state in, nothing here reads the world.
The reason string arrives verbatim, and so does the advice: when a
path owes the model an imperative (the deny back-out), the caller
passes it beside the reason and it is rendered as its own sentence —
this module never invents instructions.

What the brief did not compose it labels: the walk's account carries
the agent steps' return fields — the model's transcription of whatever
the app showed — and the messages sent, so that clause wears the same
stamp the micro calls put on untrusted text (`prompts.DATA_STAMP`). The
model taking over holds every tool; the note it resumes from must not
read a seller's words as the conductor's. A model-written reason is
quoted and clipped where it enters (`steps.agent`), for the same cause.
"""

from physiclaw.conductor.micro.prompts import DATA_STAMP
from physiclaw.conductor.walk import money
from physiclaw.conductor.walk.ledger import Ledger


def walk_brief(
    reason: str,
    *,
    ledger: Ledger,
    where: str,
    consented: float | None,
    advice: str = "",
) -> str:
    """A handed-over walk's report: why, what the model taking over
    owes (`advice`, when the path left one), where (`Course.label`,
    the one prose reading of the cursor), and the walk's account
    (`Ledger.account` — the same facts every other exit reports) with
    the two money warnings that model must read."""
    parts = [f"conductor handing over: {reason}."]
    if advice:
        parts.append(f"{advice[0].upper()}{advice[1:]}.")
    parts.append(f"Walk {ledger.ref} stopped at {where}.")
    account = ledger.account()
    if account:
        parts.append(f"So far {DATA_STAMP}: " + "; ".join(account) + ".")
    if consented is not None:
        # Consent is CONSUMED by firing (program.py), so a consented
        # value surviving to the brief proves the payment did NOT fire.
        parts.append(
            f"The user consented to {money.plain(consented)}; the payment has NOT been made."
        )
    if ledger.paid is not None:
        parts.append(
            f"A payment of {money.plain(ledger.paid)} was FIRED before this stop and its result "
            f"is unverified — {money.VERIFY_AFTER_PAY}."
        )
    parts.append(
        "The synthesized turns above are the walk so far; this turn's "
        "peek shows the current screen. Verify state before acting."
    )
    return " ".join(parts)


def stop_recap(reason: str, *, ref: str, where: str, ledger: Ledger) -> str:
    """A stop's last word: where the walk stood, the account, and whether
    money moved — after a fired payment a stop leaves what it paid for
    unverified. The money clause is a WARNING, not a tally, which is why
    it is worded here, not by `Ledger.recap`."""
    spent = (
        f"a payment of {money.plain(ledger.paid)} fired, unverified"
        if ledger.paid is not None
        else "nothing paid"
    )
    return "; ".join([f"{ref} stopped at {where} — {reason}", *ledger.account(), spent])
