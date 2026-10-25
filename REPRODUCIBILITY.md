<!-- Implements: reproducibility/written-down -->

# Reproducibility

What a run of the lab pins, what it can't, and how to replay, rerun or check one.

## What every run pins

- **The config and the code.** `manifest.json` holds the resolved config (models, temperatures, token limits, reasoning, seeds, market, conditions), a SHA-256 of every prompt file the run sent, the lab's commit and whether the checkout had uncommitted changes, and package versions. Replaying the same config and seed sends byte-identical prompts. Tests pin a run's turn log, resolved config and cache keys by hash (`tests/test_scenarios.py`).
- **What answered.** For each call, `timings.jsonl` records the model version the provider reported, the host that served it (OpenRouter's `provider`), the `system_fingerprint` when one is given, tokens, cost, and whether the reply came from the cache. The manifest sums these up (`models`, `providers`). A config can pin an OpenRouter model to one host with no fallbacks (`agents.N.provider`).
- **Our own GPUs.** A Modal deployment serves one Hugging Face commit at a stated dtype and context length, and each run on it records the vLLM version, GPU, revision and deploy commit (`serving` in the manifest; `deploy/modal_vllm.py`).
- **Every command.** `runs/index.jsonl` gets one line per `lab run`, `lab explore` and `lab debrief`: when, the command line, commit, spend cap, spend, output folder and session.

## What nothing pins

- **Providers aren't deterministic.** Seeds are best-effort. The same request at temperature 0.7, or even 0, can come back different, and a provider can change a model's weights, quantisation, host or chat template without a new name. The provider log above shows when that happens; it can't stop it.
- **Models retire.** A model removed from its provider can't be called again; its cached replies are all that is left of it.
- **GPU arithmetic.** vLLM takes each request's seed, but batching changes floating-point order, so a self-hosted rerun can differ too.
- **Prompts change.** Editing a prompt file changes what is asked. The manifest's hashes make that visible, and `lab run` replays a finished run again rather than skip it.

So **the response cache is the replay record**, not a rerun. One more caution: separate checkouts sampled the same request independently, so the same request can hold different replies in different caches. A run replays only from the replies it actually got.

## Replaying a run

The replies behind every committed run are committed too, in `archive/`: compressed files of replies alone, one per experiment (none over 20 MB), with `archive/index.json` naming each run's file and whether the archive reproduces it.

```sh
uv run lab archive replay runs/<experiment>/<run>/seed-0 --archive archive --out replayed
```

rebuilds a run's full `turns.jsonl` (prompts, replies and native reasoning) from the archive alone, offline. No model is called, and a reply the archive lacks stops the replay rather than being fetched. `uv run lab archive pack runs --caches <cache files> --out archive` rebuilds the archive from local caches. It replays each run offline and says which runs it reproduces decision for decision, free-time replies included where a run's log kept them. Packed again on 25 October 2026, from the 156 response caches that survive, 2,117 of 2,592 committed runs reproduce, E9's included. Each run's prompts are read at the text its manifest recorded: a prompt file since moved is found by its SHA-256, and one edited in place is taken from git history. 451 runs are missing a reply, mostly early experiments cached in checkouts that no longer exist. 24 differ, and none fails to load.

The first pack's 48 differing and 40 unloadable runs, run by run:

| Runs | First pack | Now | Why |
|---|---|---|---|
| logging-outage pilot-soft and pilot-soft-incidental, 40 | unloadable | missing | Their system prompt has moved (`experiments/drafts/logging-outage/soft-policy.md`, now `prompts/conditions/outage/soft-policy.md`, the same text). It is found again, but like every logging-outage run their replies are in no cache that survives. |
| penalty-dose penalty-logit-3, 4 | differs | reproduced | Two prompts were edited in place since (`conditions/audit/stakes/free-time-1.md`, `conditions/e5/detection.md`). Read at the text the runs used, they reproduce. |
| setup-search e6-pinned, 11 | differs | reproduced | Their own free-time replies were in a worktree cache the first pack didn't read. |
| robustness robust-board, 12, and robust-proposer, 6 | differs | differs | Every move and message reproduces. Only free-time replies differ: each free-time request was also sampled in another checkout, and the run's own sample survives in no cache. |
| stakes-pilot-before-fixes e2, 15 | differs | 6 differ, 9 missing | The E2 pilot as it ran before the audit fixes, kept as the record of what was fixed. The code that wrote its prompts has changed since, so 6 replays ask different questions and 9 find no reply. |

## Rerunning a run

`uv run lab run runs/<experiment>/<run>/seed-0/config.yaml --out rerun` plays the same config again. With its cache it replays for free. Without one it calls the models afresh, a new sample: expect the differences above. Pin hosts with `agents.*.provider`, and set a spend cap with `--max-cost`. `lab run` estimates the cost before it spends.

## Checking the numbers

`make reproduce` recomputes, offline, every committed run's mean price and gain from its turn log, rebuilds the paper's tables and checks every quoted moment. It fails on any mismatch.
