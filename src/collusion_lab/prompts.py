# Implements: agents/prompt-templates
"""Prompt templates: files in prompts/ with `$placeholders` filled from the game.

Templates use `string.Template`, so JSON braces in a prompt need no escaping.
Apart from the placeholders, the model reads the file exactly as written, which
is why prompt files carry no comments (they're traced by their spec rows). An
unknown placeholder stops the run rather than leaving `$name` in a prompt.
"""

import string
from pathlib import Path


class PromptError(ValueError):
    """A prompt template that can't be filled."""


def render(prompts_dir, name, values):
    text = Path(prompts_dir, name).read_text()
    try:
        return string.Template(text).substitute(values)
    except KeyError as error:
        raise PromptError(f"{name}: unknown placeholder ${error.args[0]}.") from error
    except ValueError as error:
        raise PromptError(f"{name}: {error}.") from error
