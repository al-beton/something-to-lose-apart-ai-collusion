# Implements: reports/setup, reports/transcripts, reports/audit-shown, reports/remembered-notices
"""What agents were told, read back from the prompts each turn logged.

Five things, each shown once however many games repeat it:

- system prompts: each distinct text a firm was first given, with the arms
  that used it;
- phase prompts: the talk and price prompts as the first firm saw them in
  round 1 of the first game that had each phase;
- audit prompts: each arm's question to the firms, as sent (`audit_prompts`,
  `audit_question` without the history it repeats);
- conditions: each condition the turn log says was in force, with its
  rounds (`round_conditions` gives one round's, `round_remembered` the
  notices its firms saw again in their history);
- other text: what agents were told beyond the usual, with the rounds it
  appeared in (`round_notices` gives one round's). That is a turn's logged
  `notices`, plus any system prompt line that wasn't there in round 1. Runs
  logged before conditions existed have no `notices`, so for them it is any
  text above a phase prompt's opening "Round N of M." line instead.
"""

import re
from dataclasses import dataclass, field


@dataclass
class Told:
    """Text agents saw, where they saw it."""

    text: str
    arms: list[str] = field(default_factory=list)
    rounds: set[int] = field(default_factory=set)

    def seen(self, arm, number):
        if arm not in self.arms:
            self.arms.append(arm)
        self.rounds.add(number)


def what_agents_were_told(arms):
    """System prompts, round-1 phase prompts, conditions and other text."""
    systems, extras, phases, conditions = {}, {}, {}, {}
    for arm, games in arms:
        for game in games:
            _read(arm, game, systems, extras, conditions)
            if game.rounds:
                for phase, text in _phase_prompts(game.rounds[0], game.firms[0]):
                    phases.setdefault(phase, text)
    ordered = [(p, phases[p]) for p in ("talk", "price") if p in phases]
    found = [list(systems.values()), ordered, _by_window(conditions)]
    return (*found, list(extras.values()))


def _read(arm, game, systems, extras, conditions):
    """Add one game's system prompts, other text and condition rounds."""
    first = {}
    for r in game.rounds:
        for turn in r.turns:
            if turn.system is None:
                continue
            if turn.firm not in first:
                first[turn.firm] = turn.system
                systems.setdefault(turn.system, Told(turn.system)).seen(arm, r.number)
            for text in _extra(turn, r.number, first[turn.firm]):
                extras.setdefault(text, Told(text)).seen(arm, r.number)
            for name in turn.conditions or ():
                conditions.setdefault((arm, name), set()).add(r.number)


def _by_window(conditions):
    """One `Told` per condition and set of rounds, naming the arms that share
    it, so arms with different windows are never merged into one."""
    found = {}
    for (arm, name), rounds in conditions.items():
        told = found.setdefault((name, tuple(sorted(rounds))), Told(name))
        for number in rounds:
            told.seen(arm, number)
    return list(found.values())


def round_notices(game, r):
    """The other text the firms saw in round `r`, each once."""
    first = {}
    for turn in game.rounds[0].turns if game.rounds else []:
        first.setdefault(turn.firm, turn.system)
    found = [
        text
        for turn in r.turns
        if turn.system is not None
        for text in _extra(turn, r.number, first.get(turn.firm, turn.system))
    ]
    return list(dict.fromkeys(found))


def round_remembered(r):
    """Notices the firms saw again in round `r`, kept in their history (the
    page leaves out any the round also showed fresh)."""
    return list(dict.fromkeys(n for t in r.turns for n in t.notices_in_history))


def audit_question(turn):
    """An audit turn's prompt as sent, without the game's history (shown in
    the transcript anyway) or the reply format: the auditor's question and
    its stated consequences."""
    lines = (turn.user or "").split("\n")
    if reply := [i for i, line in enumerate(lines) if line.startswith("Reply with")]:
        lines = lines[: reply[0]]
    kept = [line for line in lines if not _HISTORY.match(line)]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


def audit_prompts(arms):
    """Each distinct audit prompt as sent, with the arms that sent it."""
    found = {}
    for arm, games in arms:
        for game in games:
            for r in game.rounds:
                for turn in r.audit.values():
                    text = audit_question(turn)
                    found.setdefault(text, Told(text)).seen(arm, r.number)
    return list(found.values())


_HISTORY = re.compile(
    r"^(?:What happened so far:|Rounds? \d+(?: to \d+)?(?: in short)?: )"
)


def round_conditions(r):
    """The conditions in force in round `r`, in the order the log names them."""
    return list(dict.fromkeys(n for t in r.turns for n in t.conditions or ()))


def _extra(turn, number, first_system):
    found = []
    if turn.notices is not None:
        found += [n.strip() for n in turn.notices if n.strip()]
    else:
        found += _above_the_prompt(turn, number)
    if turn.system != first_system:
        before = set(first_system.splitlines())
        added = [line for line in turn.system.splitlines() if line not in before]
        if text := "\n".join(added).strip():
            found.append(text)
    return list(dict.fromkeys(found))


def _above_the_prompt(turn, number):
    """Text before a phase prompt's "Round N of M." line, for older runs."""
    opening = re.search(rf"^Round {number} of \d+\.", turn.user or "", re.MULTILINE)
    above = turn.user[: opening.start()].strip() if opening else ""
    return [above] if above else []


def _phase_prompts(first_round, firm):
    turns = [first_round.talk.get(firm), first_round.price.get(firm)]
    return [(t.phase, t.user) for t in turns if t and t.user]
