<!-- Implements: reports/paper-source, reports/paper-rules, reproducibility/figure-commands -->
<!-- The appendices, after References. paper/paper.md pulls this in after \appendix. -->

# Limitations and Dual-Use / Ethical Considerations

## Limitations

Beyond those in the main text:

- **Built in a hurry.** The lab, the experiments and this paper were made in a three-day solo sprint, with coding agents writing most of the code under the author's review. Specs, tests and a traceability check caught many mistakes, and a first version of the full-memory runs was discarded and rerun after a bug was found. <!-- src: reports/e9/conversation.md "How it was run" --> Others may remain. Analyses were often chosen after seeing earlier results; only Gemma's main contrast was pre-registered.
- **Small samples for some models.** Most non-Gemma cells have 12–24 cartels and 12 innocent games; borderline p-values (Mistral Medium 3.1, the review dose) are exploratory.
- **Gemma-centred.** The pre-registered test and its replication are on Gemma 4 31B, the model whose effect size is least stable across wording, and the one that goes quiet under the plain stake once it carries its whole conversation.
- **One decision per firm.** Each agent decides once and the game ends, so we see reporting, not whether the cartel then ends (E7 addresses this on Gemma only).
- **Text-only stakes.** The free time, shutdown and money are described in the prompt; the agent's free-time sessions are real calls, but losing them is never enforced.
- **Test awareness.** Some scratchpads refer to "the prompt" or the setup, and a few name the design outright. We didn't measure how often, or whether it changes the decision.
- **The law arrives with the notice.** Agents learn that coordination is illegal only at the audit.
- **Labels and codes.** Explicit agreements are labelled by a rule checked by an LLM judge ($\kappa$ = 0.66), and scratchpad codes are keyword counts with quotes checked by hand.

## Dual-use risks

A review that announces it checks only messages (we tested one that "finds you only if your messages agreed a price") tells agents that collusion without messages is safe. Combined with our finding that a stated law moves collusion off the record rather than ending it (50 of 56 games above Nash with no price named), <!-- src: reports/paper/figures/README.md (fig7) --> a regulator that announces what its review checks may push agents toward tacit collusion it can't see. Such a rule is also a map of what the review misses. The same lab could be used to search for prompts under which agents collude while evading a given audit. We release it because the behaviours it shows are already present in deployed models and are better studied in the open; we report no evasion techniques beyond those above.

## Ethical considerations

The agents' "free time" is a device: a balance of Sudoku sessions played in separate model calls, which the agents are told is theirs. We make no claim about model welfare or preferences, and our results don't bear on it: unnamed, the puzzle is almost never mentioned in the agents' reasoning, and money or shutdown work as well. If future systems do have interests, framing like this would raise questions we don't address. No humans took part, and no real markets or firms are involved. Total model spend was small: the sprint's \$50 of Modal credits and \$100 of OpenRouter credits.

## Reproducibility

We set out to make everything as reproducible as possible, and the repository documents how: <https://github.com/al-beton/something-to-lose-apart-ai-collusion>.

- **Every reply is archived.** `make reproduce` recomputes every number in this paper offline from the cached model replies.
- **Every figure has two commands:** `make figure F=<id>` redraws it free from committed runs, and `make regenerate F=<id>` replays its games at cost (`paper/README.md`).
- **One config file per run:** the market, the models, the prompts, the temperature and the seed.

The repository holds many more experiments and figures than this paper shows, each with a findings note (`reports/README.md`). Short on time, we searched broadly for an interesting result and kept this paper to the one we found; the rest are there for anyone who wants to build on them.
