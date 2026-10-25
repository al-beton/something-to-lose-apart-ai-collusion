# Implements: conditions/free-time-reasoning, conditions/audit-full-history, conditions/hook-points, conditions/outage-once-remembered, conditions/adding-a-condition, conditions/switchable, conditions/audit-remembered, conditions/free-time, conditions/audit-balanced-draws, conditions/free-time-pays-last, conditions/leniency, conditions/offer, conditions/restart
"""Scenario conditions: named, switchable changes to what agents are told.

A config's `conditions:` block maps a condition's name to its settings, for
example `outage: {enabled: true, start: 8, end: 10}`; every setting is a
path like any other, so `conditions.outage.enabled: [false, true]` sweeps it.
Conditions that aren't enabled do nothing at all.

Each game plays with its own copy of every enabled condition, so a condition
may keep state for the game it is in. The game calls each one at these
points, in config order:
- `begin(config, seed, conditions)`: once, before anything else, with the
  game's config and its (begun or not yet begun) copies of every condition,
  so one condition can reach another (the audit takes free time away);
- `system(render)`: text added, after a blank line, to every agent's system
  prompt;
- `round_start(number, render)`: a notice shown before the round's first phase;
- `before_phase(number, phase, render)`: a notice shown before that phase;
- `after_round(record)`: sees the round just played (prices, profits, what
  was said); its return is ignored;
- `phase_after(number)`: a `Phase` the condition adds after that round
  (number 0: before round 1), a list of them played in order, or None; each agent then gets one turn, or
  `Phase.sessions[agent]` turns, whose user message is
  `phase_prompt(number, render, values)`, where `values` are that agent's
  usual prompt values (`$history` and so on) plus `agent` (its id) and
  `session` (which of its turns this is); replies are read by
  `agents.parse_reply` under the phase's name;
- `after_phase(number, turns, render)`: once a phase it added after round
  `number` has been played, with every turn so far;
- `replaced()`: firms a scripted player now plays, as {agent: model}; the
  game hands each over before its next round;
- `in_history(agent, turns, render)`: lines kept in that agent's history
  for its later turns (each a string), given the turns played so far;
- `summary(turns, market)`: the condition's results for `summary.json`, under
  its name, or None.
The notice hooks return the text to show, or None. `render(name, values)` fills a prompt
file from `prompts/` with the condition's own values. `active(number)` says
whether the condition is in force that round, for the turn log.
`keeps_notice()` says whether a round-start notice it gave stays in agents'
history for every later turn while it is active. `replay_seed()` is a seed
the game asks every turn with, but those of phases marked `resampled`, in
place of its own (a recorded game replayed, as `restart` does), or None.

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
    memory: bool = False  # show the agent's memory, as on its next move turn
    resampled: bool = False  # asked with the game's own seed (replay_seed)
    reasoning: str | None = None  # in place of the agent's own reasoning level

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

    def begin(self, config, seed, conditions):
        return None

    def after_phase(self, number, turns, render):
        return None

    def replaced(self):
        return {}

    def replay_seed(self):
        return None

    def pinned(self, config):
        """This condition as one game of `config` writes it in its own config:
        anything it needs from the whole run (all its seeds) kept."""
        return self

    # Settings left out of a written config while at these defaults, so
    # configs written before they existed still match.
    quiet = ()  # (setting, default) pairs
    # Asked for its phases after every other condition, whatever the config
    # order: free time pays out only once an audit has taken its share.
    pays_last = False

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
from collusion_lab.conditions import (  # noqa: F401
    audit,
    free_time,
    instruction,
    leniency,
    offer,
    outage,
    restart,
)
