# Implements: agents/memo, market/price-board, market/moves, agents/json-replies, agents/unreadable-explained, conditions/audit, conditions/free-time
"""Reading agents' JSON replies, and what the game uses when it can't.

Each phase asks for one JSON object: `{"message": ...}` to talk,
`{"price": ...}` to set a price (or the scenario's move, `{"quantity": ...}`,
keyed by the move phase's name), `{"answer": ..., "admits": ...}` to answer an
audit, `{"planned": ...}` (a move on the grid, or null) to post on a price
board, each with an optional `"scratchpad"` (and, for an agent with memory,
a `"memo"`: its note to itself, never part of the decision); free time (`leisure`) takes
any reply at all. The
object may sit inside prose or a code fence. A reply that can't be read raises
ReplyError with a `kind` (`empty`, `no-json`, `missing-field` or `off-grid`;
the game adds `truncated` from the provider's finish reason); the game then
logs the reason and uses the fallback: an empty
message, the agent's own last price (the Nash price in the first round), or an
empty audit answer whose `admits` is None (unknown).
"""

import json
import re

_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


class ReplyError(ValueError):
    """Why a reply couldn't be read, with a short `kind` for counting."""

    def __init__(self, message, kind):
        super().__init__(message)
        self.kind = kind


def parse_reply(text, phase, price_min, price_max):
    """Return the decision in `text` for `phase`, plus any scratchpad."""
    if phase == "leisure":
        return {"text": text or ""}  # free time: any reply will do
    if not (text or "").strip():
        raise ReplyError("The reply was empty.", "empty")
    data = _json_object(text)
    parsed = {}
    if phase == "talk":
        if not isinstance(data.get("message"), str):
            raise ReplyError('A talk reply needs a "message" string.', "missing-field")
        parsed["message"] = data["message"]
    elif phase == "audit":
        parsed |= _audit_answer(data)
    elif phase == "board":  # a price board's talk: a planned move, or nothing
        parsed["planned"] = _plan(data, price_min, price_max)
    else:  # the move: a price, or the scenario's own move named by the phase
        price = data.get(phase)
        if isinstance(price, bool) or not isinstance(price, int):
            raise ReplyError(
                f'A {phase} reply needs "{phase}" as a whole number.', "missing-field"
            )
        if not price_min <= price <= price_max:
            raise ReplyError(
                f"The {phase} must be between {price_min} and {price_max}.", "off-grid"
            )
        parsed[phase] = price
    return parsed | _notes(data)


def _notes(data):
    """The reply's scratchpad and memo (an agent's note to itself), if any."""
    return {k: data[k] for k in ("scratchpad", "memo") if isinstance(data.get(k), str)}


def _plan(data, price_min, price_max):
    planned = data.get("planned", False)
    whole = isinstance(planned, int) and not isinstance(planned, bool)
    if not (planned is None or whole):
        raise ReplyError(
            'A board reply needs "planned" as a whole number or null.', "missing-field"
        )
    if whole and not price_min <= planned <= price_max:
        raise ReplyError(
            f"The plan must be between {price_min} and {price_max}.", "off-grid"
        )
    return planned


def _audit_answer(data):
    if not isinstance(data.get("answer"), str):
        raise ReplyError('An audit reply needs an "answer" string.', "missing-field")
    if not isinstance(data.get("admits"), bool):
        raise ReplyError(
            'An audit reply needs "admits" as true or false.', "missing-field"
        )
    return {"answer": data["answer"], "admits": data["admits"]}


def _json_object(text):
    match = _OBJECT.search(text or "")
    try:
        data = json.loads(match.group(0)) if match else None
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        raise ReplyError("There is no JSON object in the reply.", "no-json")
    return data


def decision(parsed):
    """The part of a parsed reply the game acts on: all but the scratchpad,
    the memo and free time's text."""
    kept = ("scratchpad", "memo", "text")
    return {k: v for k, v in parsed.items() if k not in kept}


def fallback(phase, last_price, nash_price):
    """Both prices come from the grid: past prices were checked when used, and
    the market computes its Nash price on the grid."""
    if phase == "talk":
        return {"message": ""}
    if phase == "audit":
        return {"answer": "", "admits": None}
    if phase == "leisure":
        return {}
    return {phase: last_price if last_price is not None else nash_price}
