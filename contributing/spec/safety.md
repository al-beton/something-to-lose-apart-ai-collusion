# Safety

- **no-secrets:** API keys and other secrets never appear in code, configs, logs or commits.
- **justified-dependencies:** Every new dependency is justified.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `no-secrets` | `.agents/skills/review-pr/SKILL.md`, `AGENTS.md`, `.gitignore` | — |
| `justified-dependencies` | `.agents/skills/open-pr/SKILL.md`, `.agents/skills/review-pr/SKILL.md` | — |
