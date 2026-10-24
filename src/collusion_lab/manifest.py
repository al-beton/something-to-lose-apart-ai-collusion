# Implements: reproducibility/manifest, runs/resume, runs/per-firm-summary
"""What produced a run: config, prompt hashes, code, packages, models, spend.

Written as `manifest.json` next to each run's logs. Unlike `turns.jsonl`, it
holds things that vary between identical runs (times, cache hits, cost), so
the turn log stays byte-identical on replay. `agent_cost` splits `cost` by
agent; a resumed run's runner adds `earlier_cost` and `earlier_agent_cost`,
what earlier attempts spent.
"""

import hashlib
import importlib.metadata
import platform
import subprocess
from pathlib import Path

from collusion_lab.backends import is_mock

PACKAGES = ("collusion-lab", "litellm", "pyyaml")


def build(config, prompt_names, calls, started, finished):
    paid = [c for c in calls if not is_mock(c["model"])]
    models = {}
    for call in paid:
        if call["model_version"]:
            models.setdefault(call["agent"], set()).add(call["model_version"])
    usage = [c["usage"] for c in paid if c["usage"]]
    fresh = [c for c in paid if not c["cached"]]
    unpriced = [c for c in fresh if c["cost"] is None]
    return {
        "config": config.to_dict(),
        "prompts": {
            name: _hash(Path(config.prompts_dir, name)) for name in prompt_names
        },
        "code": _code(),
        "packages": _packages(),
        "models": {agent: sorted(v) for agent, v in sorted(models.items())},
        "calls": len(paid),
        "cache": {
            "hits": sum(1 for c in paid if c["cached"]),
            "misses": sum(1 for c in paid if not c["cached"]),
        },
        "tokens": {
            "prompt": sum(u["prompt_tokens"] for u in usage),
            "completion": sum(u["completion_tokens"] for u in usage),
        },
        # Cache hits cost nothing; a fresh call LiteLLM can't price makes the
        # total unknown rather than silently zero.
        "cost": None if unpriced else sum(c["cost"] or 0 for c in fresh),
        "unpriced_calls": len(unpriced),
        "agent_cost": _agent_cost(fresh),
        "started": started,
        "finished": finished,
    }


def prompts_unchanged(record, prompts_dir):
    """Whether every prompt file a run used still reads as it did then."""
    for name, digest in record.get("prompts", {}).items():
        path = Path(prompts_dir, name)
        if not path.exists() or _hash(path) != digest:
            return False
    return True


def _agent_cost(fresh):
    """What each paid agent's fresh calls cost, for per-firm summaries."""
    cost = {}
    for call in fresh:
        cost[call["agent"]] = cost.get(call["agent"], 0) + (call["cost"] or 0)
    return cost


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _code():
    """The lab's own commit: git is asked about this package's folder, not the
    working directory, which may be another repository holding the configs.
    An installed copy outside a checkout reports None."""
    source = Path(__file__).resolve().parent

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(source), *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    try:
        return {
            "commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain")),
        }
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "dirty": None}


def _packages():
    versions = {"python": platform.python_version()}
    for name in PACKAGES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions
