# Implements: conditions/instruction
"""`instruction`: one prompt file added to every agent's system prompt."""

from dataclasses import dataclass

from collusion_lab.conditions import Condition, register


@register
@dataclass(frozen=True)
class Instruction(Condition):
    prompt: str = "conditions/no-collusion.md"

    name = "instruction"

    def system(self, render):
        return render(self.prompt, {})
