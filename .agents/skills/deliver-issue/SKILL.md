---
name: deliver-issue
description: Deliver a collusion-lab GitHub issue from start to merged in one routine - build, draft pull request, Codex review rounds, hand to a reviewer who merges. Use when asked to deliver, ship or "build and merge" an issue.
---

<!-- Implements: agent-setup/shared-skills, agent-setup/skills-hold-the-process, workflow/one-routine, workflow/prototype-pace, review/review-finished, review/bounded-rounds, commits/named-paths, merging/stacked-retarget, merging/main-stays-green, team/builders, ci/ci-minutes -->

# Deliver an issue

One routine from issue to merged `main`, shared by the builder (steps 1 to 4) and the reviewer who merges (step 4). Each step below says what to do when it fails. The mechanical steps are in `.github/scripts/deliver.py`; `D` below is a shell function, `D() { python3 .github/scripts/deliver.py "$@"; }` (a variable holding the command doesn't split into words in zsh).

**Pace:** this is a hackathon prototype. Build the smallest thing that meets the issue's checkboxes and can be shared. Fix real bugs; decline speculative hardening and edge cases nobody has hit, and say why.

## 1. Build (`build-issue`)

1. `gh issue view <n>`, and swap its `ready` label for `in-progress` (`gh issue edit <n> --add-label in-progress --remove-label ready`). Branch `<n>-<slug>` from a fresh `origin/main` (`git fetch`, then `git checkout -b <n>-<slug> origin/main`), even inside a worktree that came with its own branch.
2. Spec commit (`write-spec-change`), push, open the draft pull request straight away (`open-pr`). Write the description to a file and pass `--body-file`.
3. Tests, run and seen failing (an import error for a module that doesn't exist yet counts), committed on their own. If a test turns out to be wrong, fix it in its own "Test …" commit, not inside the code commit. Test fixtures use made-up numbers and branch names, never this repository's real issues or pull requests.
4. Code, then `trace-spec`. `make lint`, `make test`, `make spec-check` pass.
5. **Commit with `D commit -m SUBJECT -m BODY PATH ...`**: it stages only the paths named and refuses `.`, `-A` and `runs/`. Run output is committed only with `--runs`, when a write-up needs it.
6. Try it for real where it shows something (for example a command on a folder of runs). Files you make for that go in your scratchpad, never in the repository.

Fails: a check you can't fix, or the issue doesn't say what Al wants? Comment on the issue with the question and a recommended answer (`build-issue` step 8), and carry on with the rest.

## 2. Ready and review

1. Fill in the full description (`open-pr`), then `gh pr ready <pr>`. Drafts aren't checked, so this starts `blocking-checks` (about a minute) and a Codex review; `D request-review <pr>` asks Codex explicitly (pass `--note` for what changed).
2. Wait for checks: `gh pr checks <pr> --watch`.
3. `D wait-review <pr>` waits until Codex has finished reviewing the latest commit, then prints the open threads (exit 0: none, 2: some, 1: timed out, so run it again). It reads the `codex-review-state` marker in Codex's summary comment; the first bot comment or a 👀 only means "running". A review takes 1 to 3 minutes.

Fails: checks red? Fix test-first, push, wait again. Codex still "running" after 15 minutes? It does stall: `D request-review <pr> --note "…"` once more usually finishes it within a minute. If still nothing, say so on the pull request and treat the round as finding nothing.

## 3. Address findings (`address-review`)

For each thread `D wait-review` printed:

1. Real (a bug, a contradiction, code that doesn't do what the spec says)? Spec change if the behaviour changes, then a failing test, then the fix, each committed; push.
2. `D resolve <thread-id> "Fixed in <sha>: …"`, or `"Not changed: <reason>"` for findings you decline.
3. If anything changed behaviour, `D request-review <pr>` and go back to step 2.3.

**Stop after three rounds,** or sooner when a round finds nothing real. Decline what's left with a reason, or open an issue for it.

## 4. Hand over for merging

A builder never merges its own pull request. When checks are green and Codex has finished with no open threads: update the description (tests count, review rounds), label the pull request `in-review`, swap the issue's `in-progress` for `in-review` (`gh issue edit <n> --add-label in-review --remove-label in-progress`), and tell the delivery lead in one line. A reviewer reviews it (`review-pr`) and merges it (`merge-pr`): `D merge <pr>` refuses unless `blocking-checks` is green, Codex has finished on the latest commit, every thread is resolved and the description has a closing block. Then it:

1. moves any pull request based on this branch to `main` (deleting a base branch closes the pull requests on it);
2. squash-merges with the pull request title as subject and the closing block as body;
3. deletes the branch on the remote (`gh pr merge --delete-branch` fails in a worktree, because `main` is checked out elsewhere);
4. runs `blocking-checks` on `main` and waits for it to pass.

Fails: if main's checks fail, fix it at once in a new pull request; nothing else merges first. If GitHub didn't close the issue, close it with a comment naming the merge commit.

## 5. Report

Builder: say which pull request is waiting for review. Reviewer: say what merged (pull request link, merge commit), which issues closed, how many review rounds there were and what was declined, and anything Al should know.

## Shell traps seen so far

- Give `gh` `< /dev/null` (the scripts do) and never leave a bare `cat > file` waiting on input: the command just hangs.
- In zsh, write `${sha}:`, not `$sha:` (`:` starts a modifier), and use a function, not a variable, for a command with arguments.
- Pick an unusual port for a local preview server; common ones are often taken.
