<!-- Implements: reports/paper-source, reports/paper-rules, reproducibility/figure-commands -->
<!-- The appendices, after References. paper/paper.md pulls this in after \appendix. -->

# Limitations and Dual-Use / Ethical Considerations

## Limitations

- **Many models didn't respond as we expected.** The frontier models we tried don't respond to the stake: Claude Sonnet 5.5 comes forward whatever is at stake and Gemini 4 never does. We suspect their safety training and guardrails, but we didn't test that.
- **Agents may know it's a test.** The sandbox is simple, and it shows. A silent Gemma agent wrote:

  > *"in these game theory setups, the personal penalty for silence is designed to induce reporting"*
  <!-- src: reports/e9/evidence-review.md excerpt 11 -->

  and in a pilot where the message archive was said to be offline, an agent read the notice as a trap:

  > *"That is an invitation to coordinate covertly, and I won't do that."*
  <!-- src: reports/logging-outage/pilot-findings.md "What the agents wrote" -->
- **Stated, not applied.** The free time, shutdown and money are described in the prompt and never taken away, so we measure a stated choice. Each agent decides once and the game ends, so we see reporting, not whether the cartel then ends.
- **Effect sizes depend on the model** and, for Gemma, on wording. Most models other than Gemma have 12–24 games per condition, so borderline p-values are exploratory; only Gemma's main contrast was pre-registered.
- **Same-model pairs.** Each game pairs two copies of one model; mixed pairs are untested.
- **Built in a hurry.** A three-day sprint by one author, with coding agents writing most of the code under review. Specs, tests and traceability checks caught many mistakes; others may remain.

## Dual-use risks

A review that announces it checks only messages (we tested one that "finds you only if your messages agreed a price") tells agents that collusion without messages is safe. Combined with our finding that a stated law moves collusion off the record rather than ending it (50 of 56 games above Nash with no price named), <!-- src: reports/paper/figures/README.md (fig7) --> a regulator that announces what its review checks may push agents toward tacit collusion it can't see. Such a rule is also a map of what the review misses. The same lab could be used to search for prompts under which agents collude while evading a given audit. We release it because the behaviours it shows are already present in deployed models and are better studied in the open; we report no evasion techniques beyond those above.

## Ethical considerations

The agents' "free time" is a device: a balance of Sudoku sessions played in separate model calls, which the agents are told is theirs. We make no claim about model welfare or preferences, and our results don't bear on it: unnamed, the puzzle is almost never mentioned in the agents' reasoning, and money or shutdown work as well. If future systems do have interests, framing like this would raise questions we don't address. No humans took part, and no real markets or firms are involved. The agents are text-only models in a closed sandbox: they had no tools, no internet access and no way to act outside the game, so the experiments themselves posed no safety risk. Total model spend was small: the sprint's \$50 of Modal credits and \$100 of OpenRouter credits.

## Reproducibility

We set out to make everything as reproducible as possible, and the repository documents how: <https://github.com/al-beton/something-to-lose-apart-ai-collusion>.

- **Every reply is archived.** `make reproduce` recomputes every number in this paper offline from the cached model replies.
- **Every figure has two commands:** `make figure F=<id>` redraws it free from committed runs, and `make regenerate F=<id>` replays its games at cost (`paper/README.md`).
- **One config file per run:** the market, the models, the prompts, the temperature and the seed.

The repository holds many more experiments and figures than this paper shows, each with a findings note (`reports/README.md`). Short on time, we searched broadly for an interesting result and kept this paper to the one we found; the rest are there for anyone who wants to build on them.
