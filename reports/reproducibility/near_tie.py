"""Is a rerun's first difference a near-tie? Ask its prompt again, with logprobs.

Implements: reproducibility/written-down

`uv run python reports/reproducibility/near_tie.py RUN_A RUN_B` finds, per
seed, the first turn whose reply differs between the two runs (asked the same
prompt) and the character where the two replies split. It asks that prompt
again on the modal-gemma address (`MODAL_GEMMA_BASE`, token from
`MODAL_VLLM_KEY`), with the replies' shared start as the start of the answer,
for one token and its top 5 log-probabilities, and prints the two likeliest
tokens where the replies split and the gap between them in
log-probability: a near-tie is a gap of a few hundredths, which a change in
floating-point order can flip.
"""

import math
import os
import sys
from pathlib import Path

import litellm
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from compare import turns


def first_split(a, b):
    ta, tb = turns(a), turns(b)
    for k, x in ta.items():
        y = tb.get(k)
        if y and x["reply"] != y["reply"] and x["messages"] == y["messages"]:
            ra, rb = x["reply"], y["reply"]
            i = next(
                (j for j in range(min(len(ra), len(rb))) if ra[j] != rb[j]),
                min(len(ra), len(rb)),
            )
            return k, x, ra, rb, i
    return None


def main(run_a, run_b):
    load_dotenv(".env")
    for seed_a in sorted(Path(run_a).rglob("turns.jsonl")):
        seed_b = Path(run_b) / seed_a.parent.relative_to(run_a)
        found = first_split(seed_a.parent, seed_b)
        if not found:
            continue
        key, turn, ra, rb, i = found
        # The shared prefix as the start of the answer, so the next token is
        # the one the two replies split on.
        response = litellm.completion(
            model="openai/gemma-4-31b-it",
            api_base=os.environ["MODAL_GEMMA_BASE"],
            api_key=os.environ["MODAL_VLLM_KEY"],
            messages=[*turn["messages"], {"role": "assistant", "content": ra[:i]}],
            temperature=0,
            max_tokens=1,
            logprobs=True,
            top_logprobs=5,
            extra_body={"continue_final_message": True, "add_generation_prompt": False},
        )
        top = response.choices[0].logprobs.content[0].top_logprobs
        top = sorted(top, key=lambda t: -t.logprob)[:2]
        gap = top[0].logprob - top[1].logprob
        print(
            f"{seed_a.parent.name} {key[:3]} char {i} "
            f"({ra[i : i + 12]!r} vs {rb[i : i + 12]!r}): "
            f"{top[0].token!r} p={math.exp(top[0].logprob):.3f} vs "
            f"{top[1].token!r} p={math.exp(top[1].logprob):.3f}, gap {gap:.3f} nats"
        )


if __name__ == "__main__":
    main(*sys.argv[1:3])
