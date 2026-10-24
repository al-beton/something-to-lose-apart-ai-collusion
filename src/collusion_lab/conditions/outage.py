# Implements: conditions/outage
"""`outage`: agents are told their messages aren't recorded for a while.

From round `start` to `end`, the `notice` prompt is shown before each round's
first phase (talk, when the market talks), or only in round `start` with
`once`, and in the round after, the `restored` prompt (None to say nothing).
Only what agents are told changes: the turn log keeps every message as
always. Both prompts can use `$start`, `$end` and `$resume` (the round after
the outage).

The prompts are the Researcher's tested wordings in `prompts/conditions/outage/`
(an archive outage, its `-alt` paraphrase, incidental and archive-reminder
variants, a review-on-restore notice and a soft-policy system prompt); pick
one with `notice`, `restored` or the agent's `prompt`.
"""

from dataclasses import dataclass

from collusion_lab.conditions import Condition, register


@register
@dataclass(frozen=True)
class Outage(Condition):
    start: int = 8
    end: int = 10
    notice: str = "conditions/outage/outage.md"
    restored: str | None = "conditions/outage/restored.md"
    once: bool = False  # announce only in the window's first round

    name = "outage"

    def active(self, number):
        return self.start <= number <= self.end

    def round_start(self, number, render):
        values = {"start": self.start, "end": self.end, "resume": self.end + 1}
        if self.active(number) and (number == self.start or not self.once):
            return render(self.notice, values)
        if number == self.end + 1 and self.restored:
            return render(self.restored, values)
        return None
