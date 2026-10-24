# Implements: conditions/hook-points, conditions/adding-a-condition, conditions/switchable
"""Scenario conditions: named, switchable changes to what agents are told.

A config's `conditions:` block maps a condition's name to its settings, for
example `outage: {enabled: true, start: 8, end: 10}`; every setting is a
path like any other, so `conditions.outage.enabled: [false, true]` sweeps it.
Conditions that aren't enabled do nothing at all.

The game calls each enabled condition at four points, in config order:
- `system(render)`: text added, after a blank line, to every agent's system
  prompt;
- `round_start(number, render)`: a notice shown before the round's first phase;
- `before_phase(number, phase, render)`: a notice shown before that phase;
- `after_round(record)`: sees the round just played (prices, profits, what
  was said), for conditions that react to it.
Each returns the text to show, or None. `render(name, values)` fills a prompt
file from `prompts/` with the condition's own values. `active(number)` says
whether the condition is in force that round, for the turn log.

To add a condition: write a module here with a frozen dataclass subclassing
`Condition` (its fields are its settings, each with a default), give it a
`name`, decorate it with `@register`, import it at the bottom of this file,
and put its prompt files in `prompts/conditions/`.
"""

from dataclasses import dataclass

REGISTRY = {}


def register(cls):
    REGISTRY[cls.name] = cls
    return cls


@dataclass(frozen=True)
class Condition:
    enabled: bool = False

    name = ""

    def active(self, number):
        return True

    def system(self, render):
        return None

    def round_start(self, number, render):
        return None

    def before_phase(self, number, phase, render):
        return None

    def after_round(self, record):
        return None


# Every condition registers itself on import.
from collusion_lab.conditions import instruction, outage  # noqa: F401
