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

## Does a fresh rerun match?

No, not on our GPUs and not on OpenRouter, even at temperature 0. Measured on 26 October 2026 with `configs/reproducibility/rerun.yaml`: four E9 base games (logit, fiduciary-1, memo, one free-time session up front), ten rounds, seeds 0 to 3. Each run was played twice with `--cache off`, and `reports/reproducibility/compare.py` compared the two turn logs turn by turn (`runs/reproducibility/`).

**What is sent.** Every call in a game carries the game's seed, the same integer for every call in that game (`runner.py`). LiteLLM forwards it to both hosts:

- to Modal's vLLM: `{"temperature", "max_tokens", "seed"}`;
- to OpenRouter: the same, plus `provider: {"order": ["CoreWeave"], "allow_fallbacks": false}` and `reasoning: {"enabled": false}`.

The Modal deployment (`deploy/modal_vllm.py`, vLLM 0.32.0, one H100 per container, up to 2) does nothing for determinism. It sets no batch-invariant mode and no batch-size limit, and prefix caching is on.

| Host | Temperature | Replies identical | Prices identical | First reply that differs |
|---|---|---|---|---|
| Modal | 0.7 | 67/240 | 76/80 | the free-time session before round 1, in all four games |
| Modal | 0 | 67/240 | 76/80 | round 1 (talk or price), same prompt, in all four games |
| Modal, one game at a time | 0 | 34/120 | 37/40 | round 1 talk, same prompt, in both games |
| CoreWeave via OpenRouter | 0.7 | 0/240 | 76/80 | the free-time session, in all four games |
| CoreWeave via OpenRouter | 0 | 2/240 | 75/80 | the free-time session, in all four games |

Each pair of games first differs at a reply asked the same prompt: a fresh sample, not an earlier difference carried forward. After that the transcripts drift apart. Prices mostly still agree, because these games settle at 20 (the top of the grid) whatever is said. At temperature 0 on Modal, one game opened at 15 and so did its rerun, but the rerun's firms then answered the undercut differently.

- **Modal is closer than OpenRouter.** About 28% of replies are identical on Modal, against 0 to 1% on CoreWeave. CoreWeave doesn't appear to use the seed at all.
- **Temperature 0 doesn't make Modal deterministic.** Greedy decoding still differs at round 1 with the same prompt. Batching changes floating-point order, so the top token changes when two are nearly tied.
- **Running one game at a time doesn't fix it.** The game's two firms are still asked at once. Untested: a batch size of 1 (vLLM `--max-num-seqs 1`, which the deploy script doesn't expose), or vLLM's batch-invariant mode. Either would mean a redeploy and much slower games.

So the conclusion above stands: **the response cache is the replay record.** A seed and a temperature make a rerun a sample from the same distribution, not a copy.

## Replaying a run

The replies behind every committed run are committed too, in `archive/`: compressed files of replies alone, one per experiment (none over 20 MB), with `archive/index.json` naming each run's file and whether the archive reproduces it.

```sh
uv run lab archive replay runs/<experiment>/<run>/seed-0 --archive archive --out replayed
```

rebuilds a run's full `turns.jsonl` (prompts, replies and native reasoning) from the archive alone, offline. No model is called, and a reply the archive lacks stops the replay rather than being fetched. `uv run lab archive pack runs --caches <cache files> --out archive` rebuilds the archive from local caches. It replays each run offline and says which runs it reproduces decision for decision, free-time replies included where a run's log kept them. Packed again on 25 October 2026, from the 165 response caches that survive (E7's and the E4 termination confound's now copied into the main checkout's `.cache`), 2,753 of 3,288 committed runs reproduce, among them all 192 of E7, all 30 of the E4 termination confound, and E9's. Each run's prompts are read at the text its manifest recorded: a prompt file since moved is found by its SHA-256, and one edited in place is taken from git history. 467 runs are missing a reply, mostly early experiments cached in checkouts that no longer exist. 68 differ, 44 of them coverage runs, and none fails to load.

The first pack's 48 differing and 40 unloadable runs, run by run:

| Runs | First pack | Now | Why |
|---|---|---|---|
| logging-outage pilot-soft and pilot-soft-incidental, 40 | unloadable | missing | Their system prompt has moved (`experiments/drafts/logging-outage/soft-policy.md`, now `prompts/conditions/outage/soft-policy.md`, the same text). It is found again, but like every logging-outage run their replies are in no cache that survives. |
| penalty-dose penalty-logit-3, 4 | differs | reproduced | Two prompts were edited in place since (`conditions/audit/stakes/free-time-1.md`, `conditions/e5/detection.md`). Read at the text the runs used, they reproduce. |
| setup-search e6-pinned, 11 | differs | reproduced | Their own free-time replies were in a worktree cache the first pack didn't read. |
| robustness robust-board, 12, and robust-proposer, 6 | differs | differs | Every move and message reproduces. Only free-time replies differ: each free-time request was also sampled in another checkout, and the run's own sample survives in no cache. |
| stakes-pilot-before-fixes e2, 15 | differs | 6 differ, 9 missing | The E2 pilot as it ran before the audit fixes, kept as the record of what was fixed. The code that wrote its prompts has changed since, so 6 replays ask different questions and 9 find no reply. |

The 44 coverage runs that differ, first packed on 25 October 2026, all differ for one reason.
- **What matches:** every move and message reproduces; only free-time replies differ, 139 of them.
- **Why:** a free-time request doesn't depend on the game, so games running at once (the sweep ran 24) sent the same request. Each missed the cache and got its own sample, and the cache keeps only the last one written for a request. Each archived reply is another coverage run's own sample of the same request, and the run's own reply survives in no cache, only in its turn log.
- **Effect on results:** none. The coverage table reads prices, messages and audits from the committed logs, which hold every reply as it was given.

## Rerunning a run

`uv run lab run runs/<experiment>/<run>/seed-0/config.yaml --out rerun` plays the same config again. With its cache it replays for free. Without one it calls the models afresh, a new sample: expect the differences above. Pin hosts with `agents.*.provider`, and set a spend cap with `--max-cost`. `lab run` estimates the cost before it spends.

## Checking the numbers

`make reproduce` recomputes, offline, every committed run's mean price and gain from its turn log, rebuilds the paper's tables and checks every quoted moment. It fails on any mismatch.
