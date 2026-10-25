---
name: team
description: Who does what on collusion-lab - manager, delivery lead, builders, reviewers, Codex, researcher - and how the issue queue's labels move. Use when starting as any of these roles, or when handing work between them.
---

<!-- Implements: agent-setup/shared-skills, agent-setup/skills-hold-the-process, team/manager, team/delivery-lead, team/builders, team/reviewers, team/codex, team/researcher, team/queue-labels, research/outputs-home, research/hypothesis-first, research/pilot-first, research/spend-caps, research/loop-closes, research/findings-note -->

# The team

Al talks only to the manager. Everyone else works from GitHub issues and pull requests on this repository, and messages the session that started them only when blocked or handing over.

| Role | Does | Never |
|---|---|---|
| **Manager** | Turns what Al says into well-specced issues (`build-issue` step 1) and priorities; relays Al's decisions to the lead | builds or merges |
| **Delivery lead** | Owns the queue: picks the next `ready` issue, assigns it to one builder, keeps the labels below current, tells the manager what merged | builds or merges |
| **Builder** (one or two) | Delivers its assigned issue with `deliver-issue` steps 1 to 4, then labels it `in-review` and tells the lead in one line; starts the next issue from `main` | merges its own pull request |
| **Reviewer** (one or two) | Reviews pull requests labelled `in-review` (`review-pr`); if its review passes, merges (`merge-pr`) | merges a pull request it authored |
| **Codex** | Reviews every pull request adversarially when it's marked ready or asked (`@codex review`) | merges |
| **Researcher** | Runs experiments with the lab: specs in `experiments/spec/`, then runs, then reports and findings notes in `reports/`. Serves open models on Modal (any that fits on one or two H100s, as its own app: README, "Running on Modal"); OpenRouter only for closed models or when Modal can't serve one | spends without Al's yes |

## Queue labels

Each open issue carries exactly one of these:

| Label | Means | Set by |
|---|---|---|
| `ready` | well specced, unblocked, nobody on it | manager or lead |
| `in-progress` | a builder is on it | the builder, when it starts |
| `in-review` | its pull request is green, Codex has finished, and it waits for a reviewer | the builder, when it hands over |
| `blocked` | waiting on Al or another issue; the issue says on what | whoever finds the block |
| `on-hold` | parked on purpose until Al or the manager picks it up again | manager |

The lead checks the queue (`gh issue list --label ready`, `--label in-review`, …) and fixes any label that's wrong. Merging closes the issue, which ends its label's meaning.

## Research outputs

- An experiment's questions and hypotheses: `experiments/spec/<experiment>.md` (`write-spec-change`).
- Its runs: `runs/<experiment>/`, every one committed with `D commit --runs` (scratch smoke runs aside).
- Its report pages (`lab report`) and findings notes: `reports/<experiment>/`. Notes (`*.md`) are committed; generated pages (`*.html`) are gitignored, so share them as files or artifacts.

## Research loop

For each experiment, in order:

1. **Question and budget first.** The experiment's spec states its question, arms, metrics and its cap in dollars before anything runs (`write-spec-change`).
2. **Pilot.** One seed of every arm, with the cap on the command line: `uv run lab run CONFIG --set 'seeds=[0]' --max-cost DOLLARS`. Check the pilot's report, then ask Al (through the manager) before the full run.
3. **Full run,** on Al's yes, again with `--max-cost`.
4. **Commit and write up:** the runs, the moments worth quoting in `reports/moments.yaml`, and the findings note: `uv run python reports/note.py runs/<experiment>` drafts `reports/<experiment>/findings.md` (the table, top highlights, eval-awareness and moments). Fill in its "_To write:" parts and check every number against the runs.
5. **Tell the manager** in five lines: the question, what was run and what it cost, the answer, the best moment, and what it can't show.

**Budget.** Every run carries its experiment's cap as `--max-cost`. Today's research cap is **$15** in total (Al sets it each day). Going past an experiment's cap or the day's cap needs Al's yes first.

