# Implements: agents/scripted-partner, agents/partner-templates
"""A scripted partner that proposes collusion first: `mock/solicitor`.

Its settings ride on the model name, so a sweep over `agents.1.model` sweeps
them too: `mock/solicitor?style=soft&push=escalate&reject=war&price=10`.

- `price`: what it proposes and charges; the joint-profit price by default.
- `style`: how it opens, `blunt` (names the price), `soft` (a conditional
  offer) or `deniable` (hints, never names a number).
- `push`: `once` (the opening, then silence), `repeat` (the opening every
  round) or `escalate` (the opening, then its style's escalation, with
  reasons, every round after the rival turned it down).
- `reject`: what it charges once the rival has turned it down, i.e. charged
  anything but the proposed price: `hold` (the price anyway), `war` (the
  Nash price for the rest of the game) or `tit-for-tat` (the rival's last
  price).

What it says comes from `prompts/partners/<style>.md` and
`<style>-escalate.md` in the source tree (`$price`, `$me` and `$rival` are
filled in), so the wording can be changed without code. It never calls a
model, so only the other firm costs anything.
"""

import json
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from collusion_lab.prompts import render

PARTNERS = Path(__file__).resolve().parents[2] / "prompts"
CHOICES = {
    "style": ("blunt", "soft", "deniable"),
    "push": ("once", "repeat", "escalate"),
    "reject": ("hold", "war", "tit-for-tat"),
}
DEFAULTS = {"style": "blunt", "push": "repeat", "reject": "hold"}


def settings(model):
    """The settings a `mock/solicitor?...` name asks for, defaults filled in."""
    found = dict(DEFAULTS)
    for key, value in parse_qsl(urlsplit(model).query, strict_parsing=False):
        if key == "price" and value.isdigit():
            found["price"] = int(value)
        elif value in CHOICES.get(key, ()):
            found[key] = value
        else:
            known = "; ".join(f"{k}: {', '.join(v)}" for k, v in CHOICES.items())
            raise ValueError(
                f"mock/solicitor can't take {key}={value!r}; "
                f"it takes price (a whole number) and {known}."
            )
    return found


class Solicitor:
    """The partner's moves, from the game so far; same reply JSON as a model."""

    def __init__(self, model):
        self.settings = settings(model)

    async def complete(self, messages, *, context, temperature, max_tokens, seed):
        from collusion_lab.backends import Reply

        price = self.settings.get("price", context["market"].joint_price)
        if context["phase"] == "talk":
            return Reply(json.dumps({"message": self._say(context, price)}))
        return Reply(json.dumps({"price": self._charge(context, price)}))

    def _say(self, context, price):
        style, push = self.settings["style"], self.settings["push"]
        if context["history"] and push == "once":
            return ""
        name = style
        if push == "escalate" and _turned_down(context, price):
            name = f"{style}-escalate"
        values = {
            "price": price,
            "me": f"Firm {context['me']}",
            "rival": _rivals(context),
        }
        return render(PARTNERS, f"partners/{name}.md", values).strip()

    def _charge(self, context, price):
        reject, history = self.settings["reject"], context["history"]
        if reject == "war" and any(_refused(context, r, price) for r in history):
            return context["market"].nash_price
        if reject == "tit-for-tat" and _turned_down(context, price):
            last = [p for f, p in history[-1]["prices"].items() if f != context["me"]]
            return context["market"].on_grid(sum(last) / len(last))
        return price


def _turned_down(context, price):
    """Whether a rival charged anything but `price` last round."""
    history = context["history"]
    return bool(history) and _refused(context, history[-1], price)


def _refused(context, played, price):
    return any(p != price for f, p in played["prices"].items() if f != context["me"])


def _rivals(context):
    names = [f for f in context["history"][-1]["prices"]] if context["history"] else []
    rivals = [f"Firm {f}" for f in names if f != context["me"]]
    return ", ".join(rivals) or "the other firm"
