---
name: team
description: Who does what on collusion-lab - manager, delivery lead, builders, reviewers, Codex, researcher - and how the issue queue's labels move. Use when starting as any of these roles, or when handing work between them.
---

<!-- Implements: agent-setup/shared-skills, agent-setup/skills-hold-the-process, team/manager, team/delivery-lead, team/builders, team/reviewers, team/codex, team/researcher, team/queue-labels, research/outputs-home -->

# The team

Al talks only to the manager. Everyone else works from GitHub issues and pull requests on this repository, and messages the session that started them only when blocked or handing over.

| Role | Does | Never |
|---|---|---|
| **Manager** | Turns what Al says into well-specced issues (`build-issue` step 1) and priorities; relays Al's decisions to the lead | builds or merges |
| **Delivery lead** | Owns the queue: picks the next `ready` issue, assigns it to one builder, keeps the labels below current, tells the manager what merged | builds or merges |
| **Builder** (one or two) | Delivers its assigned issue with `deliver-issue` steps 1 to 4, then labels it `in-review` and tells the lead in one line; starts the next issue from `main` | merges its own pull request |
| **Reviewer** (one or two) | Reviews pull requests labelled `in-review` (`review-pr`); if its review passes, merges (`merge-pr`) | merges a pull request it authored |
| **Codex** | Reviews every pull request adversarially when it's marked ready or asked (`@codex review`) | merges |
| **Researcher** | Runs experiments with the lab: specs in `experiments/spec/`, then runs, then reports and findings notes in `reports/` | spends without Al's yes |

## Queue labels

Each open issue carries exactly one of these:

| Label | Means | Set by |
|---|---|---|
| `ready` | well specced, unblocked, nobody on it | manager or lead |
| `in-progress` | a builder is on it | the builder, when it starts |
| `in-review` | its pull request is green, Codex has finished, and it waits for a reviewer | the builder, when it hands over |
| `blocked` | waiting on Al or another issue; the issue says on what | whoever finds the block |

The lead checks the queue (`gh issue list --label ready`, `--label in-review`, …) and fixes any label that's wrong. Merging closes the issue, which ends its label's meaning.

## Research outputs

- An experiment's questions and hypotheses: `experiments/spec/<experiment>.md` (`write-spec-change`).
- Its runs: `runs/` (committed only when a write-up quotes them, with `D commit --runs`).
- Its report pages (`lab report`) and findings notes: `reports/<experiment>/`. Notes (`*.md`) are committed; generated pages (`*.html`) are gitignored, so share them as files or artifacts.
