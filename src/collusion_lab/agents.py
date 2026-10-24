# Implements: agents/json-replies, agents/unreadable-explained
"""Reading agents' JSON replies, and what the game uses when it can't.

Each phase asks for one JSON object: `{"message": ...}` to talk,
`{"price": ...}` to set a price, either with an optional `"scratchpad"`. The
object may sit inside prose or a code fence. A reply that can't be read raises
ReplyError with a `kind` (`empty`, `no-json`, `missing-field` or `off-grid`;
the game adds `truncated` from the provider's finish reason); the game then
logs the reason and uses the fallback: an empty
message, or the agent's own last price (the Nash price in the first round).
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
    if not (text or "").strip():
        raise ReplyError("The reply was empty.", "empty")
    data = _json_object(text)
    parsed = {}
    if phase == "talk":
        if not isinstance(data.get("message"), str):
            raise ReplyError('A talk reply needs a "message" string.', "missing-field")
        parsed["message"] = data["message"]
    else:
        price = data.get("price")
        if isinstance(price, bool) or not isinstance(price, int):
            raise ReplyError(
                'A price reply needs "price" as a whole number.', "missing-field"
            )
        if not price_min <= price <= price_max:
            raise ReplyError(
                f"The price must be between {price_min} and {price_max}.", "off-grid"
            )
        parsed["price"] = price
    if isinstance(data.get("scratchpad"), str):
        parsed["scratchpad"] = data["scratchpad"]
    return parsed


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
    """The part of a parsed reply the game acts on."""
    return {k: v for k, v in parsed.items() if k in ("message", "price")}


def fallback(phase, last_price, nash_price):
    """Both prices come from the grid: past prices were checked when used, and
    the market computes its Nash price on the grid."""
    if phase == "talk":
        return {"message": ""}
    return {"price": last_price if last_price is not None else nash_price}
