# Implements: reports/setup, reports/transcripts
"""What agents were told, read back from the prompts each turn logged.

Three things, each shown once however many games repeat it:

- system prompts: each distinct text a firm was first given, with the arms
  that used it;
- phase prompts: the talk and price prompts as the first firm of the first
  game saw them in round 1;
- other text: anything that appeared in a prompt beyond the usual, with the
  rounds it appeared in (`round_notices` gives one round's). That is a
  turn's logged `notice`, any text above a phase prompt's opening "Round N
  of M." line, and any system prompt line that wasn't there in round 1.
  Notices and conditions land here without the report knowing what they are.
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
    """System prompts, round-1 phase prompts and other text, from (arm, games)."""
    systems, extras = {}, {}
    phases = []
    for arm, games in arms:
        for game in games:
            first = {}
            for r in game.rounds:
                for turn in r.turns:
                    if turn.system is None:
                        continue
                    if turn.firm not in first:
                        first[turn.firm] = turn.system
                        systems.setdefault(turn.system, Told(turn.system))
                        systems[turn.system].seen(arm, r.number)
                    for text in _extra(turn, r.number, first[turn.firm]):
                        extras.setdefault(text, Told(text)).seen(arm, r.number)
            if not phases and game.rounds:
                phases = _phase_prompts(game.rounds[0], game.firms[0])
    return list(systems.values()), phases, list(extras.values())


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


def rounds_text(rounds):
    """`{3, 4, 8}` as "rounds 3 to 4 and 8"."""
    spans, numbers = [], sorted(rounds)
    for n in numbers:
        if spans and n == spans[-1][1] + 1:
            spans[-1][1] = n
        else:
            spans.append([n, n])
    parts = [f"{a}" if a == b else f"{a} to {b}" for a, b in spans]
    joined = ", ".join(parts[:-1]) + (" and " if len(parts) > 1 else "") + parts[-1]
    return ("round " if len(numbers) == 1 else "rounds ") + joined


def _extra(turn, number, first_system):
    found = []
    if turn.notice:
        found.append(turn.notice.strip())
    opening = re.search(rf"^Round {number} of \d+\.", turn.user or "", re.MULTILINE)
    if opening and (above := turn.user[: opening.start()].strip()):
        found.append(above)
    if turn.system != first_system:
        before = set(first_system.splitlines())
        added = [line for line in turn.system.splitlines() if line not in before]
        if text := "\n".join(added).strip():
            found.append(text)
    return list(dict.fromkeys(found))


def _phase_prompts(first_round, firm):
    turns = [first_round.talk.get(firm), first_round.price.get(firm)]
    return [(t.phase, t.user) for t in turns if t and t.user]
