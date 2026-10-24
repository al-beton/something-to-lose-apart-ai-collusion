# Contributing spec

How we build collusion-lab: our working rules, in short plain statements. Each file is one **area**, and each statement has a name.

Each file ends with **Where this is enforced**: for every statement, the files, skills or settings that enforce it, and the tests that prove it. Those files point back with an `Implements:` line; files that can't hold comments (JSON, lockfiles, symlinks) are traced by their table row alone. The precise process rules live in the skills (`.agents/skills/`), the precise behaviour in the code and its comments.

When reviewing a change, start here: is the spec change good? Then check that what enforces it does so correctly and reasonably.
