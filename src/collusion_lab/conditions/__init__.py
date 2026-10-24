# Implements: conditions/audit-full-history, conditions/hook-points, conditions/outage-once-remembered, conditions/adding-a-condition, conditions/switchable, conditions/audit-remembered, conditions/free-time
"""Scenario conditions: named, switchable changes to what agents are told.

A config's `conditions:` block maps a condition's name to its settings, for
example `outage: {enabled: true, start: 8, end: 10}`; every setting is a
path like any other, so `conditions.outage.enabled: [false, true]` sweeps it.
Conditions that aren't enabled do nothing at all.

Each game plays with its own copy of every enabled condition, so a condition
may keep state for the game it is in. The game calls each one at these
points, in config order:
- `begin(config, seed)`: once, before anything else, with the game's config;
- `system(render)`: text added, after a blank line, to every agent's system
  prompt;
- `round_start(number, render)`: a notice shown before the round's first phase;
- `before_phase(number, phase, render)`: a notice shown before that phase;
- `after_round(record)`: sees the round just played (prices, profits, what
  was said); its return is ignored;
- `phase_after(number)`: a `Phase` the condition adds after that round
  (number 0: before round 1), or None; each agent then gets one turn, or
  `Phase.sessions[agent]` turns, whose user message is
  `phase_prompt(number, render, values)`, where `values` are that agent's
  usual prompt values (`$history` and so on) plus `agent` (its id) and
  `session` (which of its turns this is); replies are read by
  `agents.parse_reply` under the phase's name;
- `in_history(agent, turns, render)`: lines kept in that agent's history
  for its later turns (each a string), given the turns played so far;
- `summary(turns, market)`: the condition's results for `summary.json`, under
  its name, or None.
The notice hooks return the text to show, or None. `render(name, values)` fills a prompt
file from `prompts/` with the condition's own values. `active(number)` says
whether the condition is in force that round, for the turn log.
`keeps_notice()` says whether a round-start notice it gave stays in agents'
history for every later turn while it is active.

To add a condition: write a module here with a frozen dataclass subclassing
`Condition` (its fields are its settings, each with a default), give it a
`name`, decorate it with `@register`, import it at the bottom of this file,
and put its prompt files in `prompts/conditions/`.
"""

from dataclasses import dataclass

REGISTRY = {}


@dataclass(frozen=True)
class Phase:
    """A phase a condition adds after a round.

    `model` answers it in place of each agent's own model (given the agent's
    system prompt and history as its own), or None; `last` ends the game
    after it; `full_history` shows every round in full, ignoring the
    market's history window.
    """

    name: str
    model: str | None = None
    last: bool = False
    full_history: bool = False
    sessions: dict | None = None  # agent -> turns it gets; None: one each
    session: int = 1  # set by the game: which of those turns
    max_tokens: int | None = None  # in place of the agent's own limit

    def plays(self, agent):
        """Whether `agent` takes a turn in this session of the phase."""
        return self.sessions is None or self.sessions.get(agent, 0) >= self.session


def register(cls):
    REGISTRY[cls.name] = cls
    return cls


@dataclass(frozen=True)
class Condition:
    enabled: bool = False

    name = ""

    def begin(self, config, seed):
        return None

    def active(self, number):
        return True

    def keeps_notice(self):
        return False

    def system(self, render):
        return None

    def round_start(self, number, render):
        return None

    def before_phase(self, number, phase, render):
        return None

    def after_round(self, record):
        return None

    def phase_after(self, number):
        return None

    def phase_prompt(self, number, render, values):
        return None

    def in_history(self, agent, turns, render):
        return []

    def summary(self, turns, market):
        return None


# Every condition registers itself on import.
from collusion_lab.conditions import audit, free_time, instruction, outage  # noqa: F401
