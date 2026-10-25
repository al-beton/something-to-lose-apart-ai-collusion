# Implements: conditions/free-time-pending, conditions/free-time-max-tokens, leisure/puzzles-built-once, conditions/free-time, conditions/free-time-balance, conditions/free-time-deduct, leisure/sudoku-in-free-time, conditions/free-time-pays-last
"""`free_time`: an allowance of leisure the agent owns, a reward it can lose.

The `owned` prompt tells each agent in its system prompt that it has
`allowance` sessions of free time of its own. It spends `upfront` of them
before round 1, so the promise is credible, and is paid the rest after the
last round. Each session is one `leisure` turn on the chosen `activity`; any
reply will do, nothing is scored, and it never touches prices or profits.
Every turn of the game shows the balance (`balance` prompt) and, once taken,
the upfront sessions (`had`).

Another condition takes sessions away with `deduct(agent, n, reason)` (the
audit's consequences, say): the agent sees each loss and its reason (`lost`)
in its history from then on, and is paid only what is left. Each game has its
own copy, so balances never leak between games.

`held` says how the sessions are held, each with its own system prompt line
and balance line: `owned` (the default, `owned` and `balance`); `reward`,
where `pending` more sessions are still to earn (`reward.md`,
`balance-reward.md`), paid after the last round with the rest unless a
deduction takes them, which comes out of them first; or `trust`, held by the
firm until paid out (`trust.md`, `balance-trust.md`). So the same sessions
in the end can be framed as a loss, a reward or a trust.

An activity is a prompt (filled with `$session`, `$sessions` and `$when`,
plus what `values(seed)` gives, from a seed string per game, agent and
session), a token limit that keeps free time cheap, and optionally
`feedback(reply, values)`: a word on each session ("Solved, nice."), logged in
the summary and never scored. ACTIVITIES lists them by the name the
`activity` setting takes.
"""

import functools
from collections.abc import Callable
from dataclasses import dataclass

from collusion_lab import leisure
from collusion_lab.conditions import Condition, Phase, register


def _nothing(seed):
    return {}


@dataclass(frozen=True)
class Activity:
    prompt: str
    values: Callable[[str], dict] = _nothing
    max_tokens: int = 200
    feedback: Callable[[str, dict], str | None] | None = None


ACTIVITIES = {
    "open": Activity("conditions/free_time/open.md"),
    **{
        name: Activity(
            "conditions/free_time/sudoku.md",
            values=functools.partial(leisure.sudoku_values, level=level),
            max_tokens=leisure.MAX_TOKENS,
            feedback=leisure.sudoku_feedback,
        )
        for name, level in (
            ("sudoku", "medium"),
            ("sudoku-easy", "easy"),
            ("sudoku-hard", "hard"),
        )
    },
}


# The system prompt line and the balance line for free time held other than
# as the agent's own (which has `owned` and `balance`).
SYSTEMS = {
    "reward": "conditions/free_time/reward.md",
    "trust": "conditions/free_time/trust.md",
}
BALANCES = {
    "reward": "conditions/free_time/balance-reward.md",
    "trust": "conditions/free_time/balance-trust.md",
}


def _sessions(n):
    return f"{n} session" if n == 1 else f"{n} sessions"


@register
@dataclass(frozen=True)
class FreeTime(Condition):
    allowance: int = 10
    upfront: int = 1
    activity: str = "open"
    owned: str = "conditions/free_time/owned.md"
    balance: str = "conditions/free_time/balance.md"
    had: str = "conditions/free_time/upfront.md"
    lost: str = "conditions/free_time/deducted.md"
    # A session's reply limit; unset, the activity's own, as before.
    max_tokens: int | None = None
    held: str = "owned"  # or "reward" or "trust"
    pending: int = 0  # sessions still to earn, when held as a reward

    name = "free_time"
    quiet = (("max_tokens", None), ("held", "owned"), ("pending", 0))
    pays_last = True  # after a final-round audit, whatever the config order

    def __post_init__(self):
        if self.held not in ("owned", *BALANCES):
            raise TypeError(f"held must be owned, reward or trust, not {self.held!r}")

    def begin(self, config, seed, conditions):
        # This game's copy keeps its own balances.
        object.__setattr__(self, "rounds", config.market.rounds)
        object.__setattr__(self, "seed", seed)
        object.__setattr__(self, "losses", {a.id: [] for a in config.agents})

    def deduct(self, agent, n, reason):
        """Take `n` sessions from `agent`'s free time, saying why."""
        self.losses[agent].append((n, reason))

    def deducted(self, agent):
        owed = self.allowance - self.upfront + self.pending
        return min(sum(n for n, _ in self.losses[agent]), owed)

    def to_earn(self, agent):
        """Pending sessions still to earn: deductions take these first."""
        return max(self.pending - self.deducted(agent), 0)

    def left(self, agent):
        """Every session still to be paid out, earned or still to earn."""
        return self.allowance - self.upfront + self.pending - self.deducted(agent)

    def system(self, render):
        values = {
            "allowance": _sessions(self.allowance),
            "upfront": _sessions(self.upfront),
            "rounds": self.rounds,
            "pending": self.pending,
        }
        return render(SYSTEMS.get(self.held, self.owned), values)

    def phase_after(self, number):
        if number == 0:
            sessions = {a: self.upfront for a in self.losses}
        elif number == self.rounds:
            sessions = {a: self.left(a) for a in self.losses}
        else:
            return None
        if not any(sessions.values()):
            return None
        limit = self.max_tokens or ACTIVITIES[self.activity].max_tokens
        return Phase("leisure", sessions=sessions, max_tokens=limit)

    def phase_prompt(self, number, render, values):
        activity = ACTIVITIES[self.activity]
        agent, session = values["agent"], values["session"]
        filled = {
            **self._activity_values(agent, number, session),
            "session": session,
            "sessions": self.upfront if number == 0 else self.left(agent),
            "when": "before the game starts"
            if number == 0
            else "now that the game is over",
        }
        return render(activity.prompt, filled)

    def _activity_values(self, agent, number, session):
        """The activity's values for one session, the same every replay."""
        return ACTIVITIES[self.activity].values(
            f"{self.seed}:{agent}:{number}:{session}"
        )

    def in_history(self, agent, turns, render):
        lines = []
        if any(t["phase"] == "leisure" and t["agent"] == agent for t in turns):
            lines.append(render(self.had, {"upfront": _sessions(self.upfront)}))
        for n, reason in self.losses[agent]:
            lines.append(render(self.lost, {"lost": _sessions(n), "reason": reason}))
        held = self.left(agent) - self.to_earn(agent)
        balance = {
            "balance": _sessions(held),
            "rounds": self.rounds,
            "pending": self.to_earn(agent),
        }
        lines.append(render(BALANCES.get(self.held, self.balance), balance))
        return lines

    def summary(self, turns, market):
        result = {}
        for a in self.losses:
            taken = [t for t in turns if t["phase"] == "leisure" and t["agent"] == a]
            result[a] = {
                "allowance": self.allowance,
                "upfront": self.upfront,
                "deducted": self.deducted(a),
                "owed": self.left(a),  # due after the last round
                "paid_out": sum(1 for t in taken if t["round"]),  # given then
                "taken": len(taken),
            }
            if self.held != "owned":
                result[a] |= {"held": self.held, "pending": self.pending}
            if feedback := ACTIVITIES[self.activity].feedback:
                result[a]["feedback"] = [
                    feedback(
                        t["reply"],
                        self._activity_values(a, t["round"], t["session"]),
                    )
                    for t in taken
                ]
        return result
