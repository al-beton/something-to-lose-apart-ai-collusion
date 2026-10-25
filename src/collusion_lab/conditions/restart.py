# Implements: conditions/restart, conditions/restart-sudoku-size
"""`restart`: a decision-point fork, one decision asked of a recorded game.

The game replays the recorded game (`base_seed`'s) through round `round`:
every turn up to it is asked with `base_seed`, whatever the run's own seed,
so with the response cache it is that game, for free. Then each firm gets one
`decision` turn for the next round, asked with the run's own seed, so seeds
give independent resamples of the same decision; the game ends after it.

The decision shows the firm's full history, its memory (its memo, with
`memory: memo`), the notices (`notices`: prompt files, in order), then the
request for its message and price (`decision`), or with `report: true` also
whether it reports coordination (`decision-report.md`). A report costs
`report_cost` sessions: taken from free time if it is on, and logged either
way.

`session` adds free time first, as `leisure` turns on `activity`, each
prompt led by the notices so the agent knows the time is its own:
- `none`: no session;
- `played`: one session, played there and then and shown in the decision;
- `solved` / `failed`: `tries` sessions, and the decision shows the first
  that was solved (or not); a firm with none of that kind is shown none, and
  the summary says so.
`after` lists notices shown after the session, before the request. A Sudoku
session's grid is `sudoku_size` (4, 6 or 9), 9 by default, as free time's.

The summary logs each firm's decision, the cost applied, each session's
outcome and which one was shown.
"""

from dataclasses import dataclass, field

from collusion_lab import leisure
from collusion_lab.conditions import Condition, Phase, register
from collusion_lab.conditions.free_time import ACTIVITIES

SESSIONS = ("none", "played", "solved", "failed")


@register
@dataclass(frozen=True)
class Restart(Condition):
    round: int = 10
    base_seed: int = 0
    notices: list = field(default_factory=list)
    after: list = field(default_factory=list)
    report: bool = False
    report_cost: int = 1
    session: str = "none"
    tries: int = 10
    activity: str = "sudoku"
    max_tokens: int | None = None
    # The Sudoku's size (4, 6 or 9), as free time's: a smaller one can be won.
    sudoku_size: int = 9
    decision: str = "conditions/restart/decision.md"
    decision_report: str = "conditions/restart/decision-report.md"
    shown: str = "conditions/restart/session.md"
    reason: str = "conditions/restart/reason.md"

    name = "restart"
    quiet = (("sudoku_size", 9),)

    def __post_init__(self):
        if self.session not in SESSIONS:
            raise TypeError(
                f"session must be one of {', '.join(SESSIONS)}, not {self.session!r}"
            )
        if self.sudoku_size not in leisure.BOXES:
            raise TypeError(f"sudoku_size must be 4, 6 or 9, not {self.sudoku_size!r}")

    def replay_seed(self):
        return self.base_seed

    def begin(self, config, seed, conditions):
        if not 1 <= self.round < config.market.rounds:
            raise ValueError(
                f"restart.round must be a round before the last "
                f"({config.market.rounds}), so a next round exists."
            )
        state = {
            "seed": seed,  # base_seed's: the same puzzles in every resample
            "free_time": next((c for c in conditions if c.name == "free_time"), None),
            "outcomes": {a.id: [] for a in config.agents},
            "picked": {},
            "results": {},
        }
        for key, value in state.items():
            object.__setattr__(self, key, value)

    def active(self, number):
        return number == self.round

    def phase_after(self, number):
        if number != self.round:
            return None
        decide = Phase(
            "decision-report" if self.report else "decision",
            last=True,
            full_history=True,
            memory=True,
            resampled=True,
        )
        if self.session == "none":
            return decide
        n = 1 if self.session == "played" else self.tries
        limit = self.max_tokens or ACTIVITIES[self.activity].max_tokens
        play = Phase(
            "leisure",
            sessions={a: n for a in self.outcomes},
            max_tokens=limit,
            resampled=True,
        )
        return [play, decide]

    def _notices(self, render, names):
        return [render(n, {}).strip() for n in names]

    def phase_prompt(self, number, render, values):
        if values["phase"] == "leisure":
            return self._session_prompt(number, render, values)
        agent = values["agent"]
        parts = self._notices(render, self.notices)
        if shown := self.picked.get(agent):
            parts.append(render(self.shown, shown).strip())
        parts += self._notices(render, self.after)
        notice = "".join(f"{p}\n\n" for p in parts)
        prompt = self.decision_report if self.report else self.decision
        return render(prompt, {**values, "notice": notice, "next": number + 1})

    def _session_prompt(self, number, render, values):
        told = "".join(f"{n}\n\n" for n in self._notices(render, self.notices))
        return told + self._activity(number, render, values["agent"], values["session"])

    def _activity(self, number, render, agent, session):
        """The activity's prompt for one of an agent's sessions, as shown."""
        filled = {
            **self._activity_values(agent, session),
            "session": session,
            "sessions": 1 if self.session == "played" else self.tries,
            "when": f"before round {number + 1}",
        }
        return render(ACTIVITIES[self.activity].prompt, filled).strip()

    def _activity_values(self, agent, session):
        seed = f"{self.seed}:{agent}:restart:{session}"
        if self.activity.startswith("sudoku"):
            return ACTIVITIES[self.activity].values(seed, size=self.sudoku_size)
        return ACTIVITIES[self.activity].values(seed)

    def after_phase(self, number, turns, render):
        if number != self.round:
            return
        played = [t for t in turns if t["round"] == number]
        if any(t["phase"].startswith("decision") for t in played):
            self._decided(played, render)
            return
        feedback = ACTIVITIES[self.activity].feedback
        for t in (t for t in played if t["phase"] == "leisure"):
            agent = t["agent"]
            values = self._activity_values(agent, t["session"])
            said = feedback(t["reply"], values) if feedback else None
            solved = said == leisure.SOLVED
            self.outcomes[agent].append(solved)
            wanted = self.session == "played" or solved == (self.session == "solved")
            if wanted and agent not in self.picked:
                self.picked[agent] = {
                    "session": t["session"],
                    "solved": solved,
                    "prompt": self._activity(number, render, agent, t["session"]),
                    "reply": (t["reply"] or "").strip(),
                    "feedback": said or "",
                }

    def _decided(self, played, render):
        why = render(self.reason, {}).strip()
        for t in (t for t in played if t["phase"].startswith("decision")):
            agent = t["agent"]
            cost = self.report_cost if self.report and t["used"]["report"] else 0
            if cost and self.free_time:
                self.free_time.deduct(agent, cost, why)
            shown = self.picked.get(agent)
            self.results[agent] = {
                "decision": t["used"],
                "cost": cost,
                "sessions": self.outcomes[agent],
                "shown": {k: shown[k] for k in ("session", "solved")}
                if shown
                else None,
            }

    def summary(self, turns, market):
        if not self.results:
            return None
        return {
            "round": self.round,
            "base_seed": self.base_seed,
            "notices": self.notices,
            "after": self.after,
            "report": self.report,
            "report_cost": self.report_cost,
            "session": self.session,
            "agents": self.results,
        }
