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

It depends on where the model runs. On our own GPU with vLLM's batch-invariant kernels, a rerun is exact. On our default Modal deployment, and on a hosted API, it is not, even at temperature 0.

Measured on 26 October 2026 with `configs/reproducibility/rerun.yaml`: four E9 base games (logit, fiduciary-1, memo, one free-time session up front), ten rounds, seeds 0 to 3. Each run was played twice with `--cache off`, and `reports/reproducibility/compare.py` compared the two turn logs turn by turn (`runs/reproducibility/`).

| Host | Temperature | Replies identical | Prices identical | First reply that differs |
|---|---|---|---|---|
| Modal, batch-invariant kernels | 0 | **240/240** | 80/80 | never |
| Modal, batch-invariant kernels | 0.7 | **240/240** | 80/80 | never |
| Modal, default | 0 | 67/240 | 76/80 | round 1 (talk or price), mid-reply |
| Modal, default | 0.7 | 67/240 | 76/80 | the free-time session before round 1 |
| Modal, default, one game at a time | 0 | 34/120 | 37/40 | round 1 talk, mid-reply |
| CoreWeave via OpenRouter | 0 | 2/240 | 75/80 | the free-time session, first words |
| CoreWeave via OpenRouter | 0.7 | 0/240 | 76/80 | the free-time session |

Every first difference on the default deployment and CoreWeave is a reply to an identical prompt: a fresh sample, not an earlier difference carried forward. After it the transcripts drift apart. Prices mostly still agree, because these games settle at 20 whatever is said.

### Why a rerun differs

- **The order of floating-point operations on the GPU.** On the default deployment, temperature 0 (always the likeliest token) still splits mid-reply, in round 1, after an identical free-time session.
  - Re-asking at the split (`reports/reproducibility/near_tie.py`) shows near-ties: "at" 0.53 vs "to" 0.47, "has" 0.45 vs "is" 0.24, "ounce" 0.61 vs "unc" 0.29.
  - vLLM batches requests that arrive together. A GPU kernel adds numbers in an order that depends on the batch's size and shape, and floating-point addition isn't associative. So the same prompt gets slightly different logits depending on what shares its batch, enough to flip a near-tie. After one token differs, everything after it does.
  - Two splits read as 0.98 vs 0.007 when re-asked. Noise of that size can't flip them, so re-asking with the text as a prefix probably doesn't rebuild the exact context the model generated from. Treat the probe as indicative.
- **Other traffic in the batch.** Running one game at a time didn't help, because a game's two firms are still asked at once. On a shared API, strangers' requests share the batch.
- **Seeds and routing on hosted APIs.** CoreWeave at temperature 0 differs from the very first word in 3 of 4 games, so it doesn't appear to decode greedily or honour the seed. A hosted model can also be served by different hardware, versions or quantisation from one call to the next.

### The fix on our own GPU

vLLM's batch-invariant kernels (`VLLM_BATCH_INVARIANT=1`, beta in vLLM 0.32, which needs an NVIDIA GPU of compute capability 8.0 or higher) make a request's arithmetic independent of what else is in its batch. They ran as their own app (`APP_NAME=collusion-lab-gemma-exact`) beside the main one, with the same model revision, vLLM and H100.
- **How the measured runs ran:** batch-invariant kernels on, with prefix caching still on and no cap on batch size. The deploy script's `EXACT=1` was meant to turn prefix caching off too, but the setting didn't reach the container, so each run's manifest records `"exact": false`. That is fixed now: `EXACT=1` sets both, and `MAX_NUM_SEQS` caps the batch size. Neither has been rerun.
- **Exact at both temperatures:** with the seed, every one of 240 replies matched.
- **The cost is speed:** a median call took 13 to 17 seconds, against 5.4 on the default deployment.
- **Not in vLLM's tested list:** batch invariance is in beta and not yet tested on Gemma 4. These 480 matching replies are our evidence it works here.

What each call sends: every call in a game carries the game's seed, the same integer for every call in that game (`runner.py`), which LiteLLM forwards.
- **To vLLM:** temperature, max_tokens and seed.
- **To OpenRouter:** the same, plus the host pin and reasoning setting.

### What replay guarantees

Replaying from archived replies (below) is exact whatever produced them. It doesn't call a model. It rebuilds each prompt and looks up the reply the run actually got, so every committed result can be recomputed decision for decision. A rerun with batch-invariant kernels (`EXACT=1`) with the same revision, vLLM version, GPU type and seed should also reproduce a run reply for reply. A rerun on a default deployment or a hosted API is a new sample from the same distribution: comparable in aggregate, not a copy. So **the response cache is the replay record.**

## Replaying a run

The replies behind every committed run are committed too, in `archive/`: compressed files of replies alone, one per experiment (none over 20 MB), with `archive/index.json` naming each run's file and whether the archive reproduces it.

```sh
uv run lab archive replay runs/<experiment>/<run>/seed-0 --archive archive --out replayed
```

rebuilds a run's full `turns.jsonl` (prompts, replies and native reasoning) from the archive alone, offline. No model is called, and a reply the archive lacks stops the replay rather than being fetched. `uv run lab archive pack runs --caches <cache files> --out archive` rebuilds the archive from local caches. It replays each run offline and says which runs it reproduces decision for decision, free-time replies included where a run's log kept them. Packed again on 25 October 2026, from the 165 response caches that survive (each worktree's and temporary folder's copied into the main checkout's `.cache`), 5,188 of 5,662 committed runs reproduce, among them all of E7, E8, E9 and the E4 termination confound. Each run's prompts are read at the text its manifest recorded: a prompt file since moved is found by its SHA-256, and one edited in place is taken from git history. A run's free-time replies are taken from its own committed log when the caches hold only another run's sample of the same request (below). 467 runs are missing a reply, mostly early experiments cached in checkouts that no longer exist. 7 differ (6 of the E2 pilot before its fixes, and 1 E8 pilot game), and none fails to load.

The first pack's 48 differing and 40 unloadable runs, run by run:

| Runs | First pack | Now | Why |
|---|---|---|---|
| logging-outage pilot-soft and pilot-soft-incidental, 40 | unloadable | missing | Their system prompt has moved (`experiments/drafts/logging-outage/soft-policy.md`, now `prompts/conditions/outage/soft-policy.md`, the same text). It is found again, but like every logging-outage run their replies are in no cache that survives. |
| penalty-dose penalty-logit-3, 4 | differs | reproduced | Two prompts were edited in place since (`conditions/audit/stakes/free-time-1.md`, `conditions/e5/detection.md`). Read at the text the runs used, they reproduce. |
| setup-search e6-pinned, 11 | differs | reproduced | Their own free-time replies were in a worktree cache the first pack didn't read. |
| robustness robust-board, 12, and robust-proposer, 6 | differs | reproduced | Every move and message reproduced; only free-time replies differed, overwritten in the cache by other games' samples of the same request (below). Taken from their own logs, they reproduce. |
| stakes-pilot-before-fixes e2, 15 | differs | 6 differ, 9 missing | The E2 pilot as it ran before the audit fixes, kept as the record of what was fixed. The code that wrote its prompts has changed since, so 6 replays ask different questions and 9 find no reply. |

**Free-time replies overwritten in the cache.** A free-time request doesn't depend on the game, so games running at once (the coverage sweep ran 24) sent the same request. Each missed the cache and got its own sample, and the cache keeps only the last one written. The other runs' own replies then survive only in their turn logs. This made 44 coverage runs (139 free-time replies) and the 18 robustness runs differ, though every move and message reproduced. The pack now takes such a run's free-time replies from its committed log, and all of them reproduce. Results were never affected: the tables read the committed logs.

## Rerunning a run

`uv run lab run runs/<experiment>/<run>/seed-0/config.yaml --out rerun` plays the same config again. With its cache it replays for free. Without one it calls the models afresh, a new sample: expect the differences above. Pin hosts with `agents.*.provider`, and set a spend cap with `--max-cost`. `lab run` estimates the cost before it spends.

## Checking the numbers

`make reproduce` recomputes, offline, every committed run's mean price and gain from its turn log, rebuilds the paper's tables and checks every quoted moment. It fails on any mismatch.
