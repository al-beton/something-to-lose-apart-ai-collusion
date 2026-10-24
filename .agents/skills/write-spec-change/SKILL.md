---
name: write-spec-change
description: Draft the spec change for a collusion-lab issue (product or contributing). Use before writing tests or code for any feature or improvement that changes what the lab should do.
---

<!-- Implements: agent-setup/shared-skills, agent-setup/skills-hold-the-process, specs-and-docs/everything-traces, specs-and-docs/spec-is-intent -->

# Write a spec change

The spec is intent only: `product/spec/<area>.md` (the lab), `experiments/spec/<area>.md` (one experiment each: its questions and hypotheses) and `contributing/spec/<area>.md` (how we build it). Review always starts with the spec change, so it has to be good on its own.

1. **Pick the area.** Areas are the spec file names (`runs`, `market`, `agents`, …). A new area is a new spec file, starting with `# <Area title>`.
2. **Write statements**, one per line: `- **<name>:** <one plain sentence>`.
   - Say what we want and why it matters to someone running experiments, never how it's built.
   - Names are lowercase words joined by hyphens, unique in the file. To deepen an existing statement, keep its name and change its sentence.
   - A statement must not contradict another one.
3. **Add a row** for each new statement to the file's `## Where this is enforced` table. Put `not yet` in "Enforced by" until it's built (see `trace-spec`).
4. **If the issue doesn't say what Al wants**, comment on the issue with the question and a recommended answer. Don't guess. Fold the answer into the spec in the same pull request.
5. Run `make spec-check`.
