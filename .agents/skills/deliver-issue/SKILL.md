---
name: deliver-issue
description: Deliver a collusion-lab GitHub issue from start to merged in one routine - build, draft pull request, Codex review rounds, merge, clean up. Use when asked to deliver, ship or "build and merge" an issue.
---

<!-- Implements: agent-setup/shared-skills, agent-setup/skills-hold-the-process, workflow/one-routine, workflow/prototype-pace, review/review-finished, review/bounded-rounds, commits/named-paths, merging/stacked-retarget, merging/main-stays-green -->

# Deliver an issue

One routine from issue to merged `main`. Each step below says what to do when it fails. The mechanical steps are in `.github/scripts/deliver.py` (`D` below stands for `python3 .github/scripts/deliver.py`).

**Pace:** this is a hackathon prototype. Build the smallest thing that meets the issue's checkboxes and can be shared. Fix real bugs; decline speculative hardening and edge cases nobody has hit, and say why.

## 1. Build (`build-issue`)

1. `gh issue view <n>`. Branch `<n>-<slug>` from a fresh `origin/main` (`git fetch`, then `git checkout -b <n>-<slug> origin/main`), even inside a worktree that came with its own branch.
2. Spec commit (`write-spec-change`), push, open the draft pull request straight away (`open-pr`). Write the description to a file and pass `--body-file`.
3. Tests, run and seen failing (an import error for a module that doesn't exist yet counts), committed on their own. If a test turns out to be wrong, fix it in its own "Test …" commit, not inside the code commit.
4. Code, then `trace-spec`. `make lint`, `make test`, `make spec-check` pass.
5. **Commit with `D commit -m SUBJECT -m BODY PATH ...`**: it stages only the paths named and refuses `.`, `-A` and `runs/`. Run output is committed only with `--runs`, when a write-up needs it.
6. Try it for real where it shows something (for example a command on a folder of runs). Files you make for that go in your scratchpad, never in the repository.

Fails: a check you can't fix, or the issue doesn't say what Al wants? Comment on the issue with the question and a recommended answer (`build-issue` step 8), and carry on with the rest.

## 2. Ready and review

1. Fill in the full description (`open-pr`), then wait for checks: `gh pr checks <pr> --watch`. They take about a minute.
2. `gh pr ready <pr>`. Marking it ready already starts a Codex review; `D request-review <pr>` asks for one explicitly (pass `--note` for what changed).
3. `D wait-review <pr>` waits until Codex has finished reviewing the latest commit, then prints the open threads (exit 0: none, 2: some, 1: timed out, so run it again). It reads the `codex-review-state` marker in Codex's summary comment; the first bot comment or a 👀 only means "running". A review takes 1 to 3 minutes.

Fails: checks red? Fix test-first, push, wait again. Codex silent after 15 minutes? Request once more; if still nothing, say so on the pull request and treat the round as finding nothing.

## 3. Address findings (`address-review`)

For each thread `D wait-review` printed:

1. Real (a bug, a contradiction, code that doesn't do what the spec says)? Spec change if the behaviour changes, then a failing test, then the fix, each committed; push.
2. `D resolve <thread-id> "Fixed in <sha>: …"`, or `"Not changed: <reason>"` for findings you decline.
3. If anything changed behaviour, `D request-review <pr>` and go back to step 2.3.

**Stop after three rounds,** or sooner when a round finds nothing real. Decline what's left with a reason, or open an issue for it.

## 4. Merge (`merge-pr`)

Only when Al has told you to merge this pull request. Update the description (tests count, review rounds), then `D merge <pr>`. It refuses unless `blocking-checks` is green, every thread is resolved and the description has a closing block. Then it:

1. moves any pull request based on this branch to `main` (deleting a base branch closes the pull requests on it);
2. squash-merges with the pull request title as subject and the closing block as body;
3. deletes the branch on the remote (`gh pr merge --delete-branch` fails in a worktree, because `main` is checked out elsewhere);
4. runs `blocking-checks` on `main` and waits for it to pass.

Fails: if main's checks fail, fix it at once in a new pull request; nothing else merges first. If GitHub didn't close the issue, close it with a comment naming the merge commit.

## 5. Report

Say what merged (pull request link, merge commit), which issues closed, how many review rounds there were and what was declined, and anything Al should know.

## Shell traps seen so far

- Give `gh` `< /dev/null` (the scripts do) and never leave a bare `cat > file` waiting on input: the command just hangs.
- In zsh, write `${sha}:`, not `$sha:` (`:` starts a modifier).
- Pick an unusual port for a local preview server; common ones are often taken.
