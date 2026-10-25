# Implements: backends/modal, backends/modal-pinned
"""An open model on Modal, behind vLLM's OpenAI-compatible server.

    uvx modal deploy deploy/modal_vllm.py

prints the address it serves at (of the form
`https://<workspace>--collusion-lab-vllm-server.us-east.modal.direct`); a
config reaches it as `api_base: <address>/v1` with `model: openai/<SERVED_NAME>`
(see `configs/modal.yaml`). Set `MODEL`, `SERVED_NAME` and `GPU` in the
environment when deploying to serve another model; they are baked into the
image, so the container serves what you deployed. Shaped on Modal's own vLLM
example (docs/examples/vllm_inference).

- Model: Mistral Small 3.2 (24B), the model the lab's cheap and stakes
  configs use through OpenRouter. About 48 GB in bf16, so it fits one H100
  (80 GB) with room for many games at once. A gated model (Gemma, Llama) also
  needs a Hugging Face token: add `modal.Secret.from_name("huggingface")`
  (holding `HF_TOKEN`) to `secrets`.
- Auth: Modal lets requests through (`unauthenticated=True`), and the
  `vllm_token.py` middleware refuses any but health checks without the token
  in the Modal secret `collusion-lab-vllm` (`VLLM_API_KEY`), on every route,
  since vLLM's own `--api-key` guards only `/v1`. The token stays in the
  environment, never on vLLM's command line, which vLLM logs. The lab sends
  it from the variable its agent's `api_key_env` names; it never goes in a
  config.
- Cost: billed by GPU time while a container is up. One starts on the first
  request (a few minutes to load the weights; the first deploy also
  downloads them to a Volume) and stops after `scaledown_window` without
  requests, so an idle deployment costs nothing.
- `target_concurrency`: how many requests one container takes before Modal
  starts another; the lab sends up to `concurrency` games times their firms.
- Pinned: the container serves one Hugging Face revision, `REVISION` (a
  commit), or the model's current commit, looked up when you deploy, at
  `DTYPE` and `MAX_MODEL_LEN`. At start-up it writes what it serves (that
  revision, the vLLM version, GPU, dtype, context length and the lab commit
  it was deployed from) where `vllm_token.py` answers `GET /provenance` with
  it, behind the token, and each run on it records that in its manifest.
  vLLM takes each request's seed, but GPU inference isn't bit-for-bit
  deterministic (batching changes the arithmetic), so a rerun can differ:
  the response cache is the replay record.
"""

import importlib.metadata
import json
import os
import subprocess
import urllib.request
from pathlib import Path

import modal

MODEL = os.environ.get("MODEL", "mistralai/Mistral-Small-3.2-24B-Instruct-2506")
SERVED_NAME = os.environ.get("SERVED_NAME", "mistral-small-3.2")
GPU = os.environ.get("GPU", "H100")
DTYPE = os.environ.get("DTYPE", "bfloat16")
MAX_MODEL_LEN = int(os.environ.get("MAX_MODEL_LEN", "16384"))
PROVENANCE = os.environ.get("PROVENANCE_FILE", "/root/provenance.json")
MINUTES = 60
PORT = 8000


def _revision():
    """The commit to serve: REVISION, else the model's current one on the Hub."""
    if revision := os.environ.get("REVISION"):
        return revision
    url = f"https://huggingface.co/api/models/{MODEL}"
    try:
        with urllib.request.urlopen(url, timeout=20) as reply:
            return json.load(reply)["sha"]
    except (OSError, ValueError, KeyError) as error:
        raise RuntimeError(
            f"Couldn't look up {MODEL}'s current commit ({error}); set REVISION."
        ) from error


def _commit():
    """The lab commit this is deployed from (DEPLOY_COMMIT inside the image)."""
    if commit := os.environ.get("DEPLOY_COMMIT"):
        return commit
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


REVISION = _revision()
DEPLOY_COMMIT = _commit()

image = (
    modal.Image.from_registry("nvidia/cuda:12.9.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install("vllm==0.21.0")
    .env(
        {
            "HF_XET_HIGH_PERFORMANCE": "1",
            "MODEL": MODEL,
            "SERVED_NAME": SERVED_NAME,
            "REVISION": REVISION,
            "DEPLOY_COMMIT": DEPLOY_COMMIT or "",
            "DTYPE": DTYPE,
            "MAX_MODEL_LEN": str(MAX_MODEL_LEN),
            "GPU": GPU,
            "PYTHONPATH": "/root",  # so vLLM can import vllm_token
        }
    )
    .add_local_file(Path(__file__).with_name("vllm_token.py"), "/root/vllm_token.py")
)
weights = modal.Volume.from_name("collusion-lab-hf-cache", create_if_missing=True)
compiled = modal.Volume.from_name("collusion-lab-vllm-cache", create_if_missing=True)

app = modal.App("collusion-lab-vllm")


@app.server(
    image=image,
    gpu=GPU,
    scaledown_window=5 * MINUTES,
    startup_timeout=20 * MINUTES,
    volumes={"/root/.cache/huggingface": weights, "/root/.cache/vllm": compiled},
    secrets=[modal.Secret.from_name("collusion-lab-vllm")],
    port=PORT,
    routing_region="us-east",
    target_concurrency=32,
    unauthenticated=True,  # vllm_token.py guards it instead
)
class Server:
    @modal.enter()
    def start(self):
        Path(PROVENANCE).write_text(json.dumps(_provenance()))
        command = [
            "vllm",
            "serve",
            MODEL,
            "--revision",
            REVISION,
            "--dtype",
            DTYPE,
            "--served-model-name",
            SERVED_NAME,
            "--host",
            "0.0.0.0",
            "--port",
            str(PORT),
            "--middleware",
            "vllm_token.require_token",
            "--max-model-len",
            str(MAX_MODEL_LEN),
        ]
        if MODEL.startswith("mistralai/"):
            # Mistral's own tokenizer and weight format, as its model card asks.
            command += ["--tokenizer-mode", "mistral", "--config-format", "mistral"]
            command += ["--load-format", "mistral"]
        self.process = subprocess.Popen(command)

    @modal.exit()
    def stop(self):
        self.process.terminate()


def _provenance():
    """What this container serves, for GET /provenance."""
    try:
        vllm = importlib.metadata.version("vllm")
    except importlib.metadata.PackageNotFoundError:
        vllm = None
    try:
        gpu = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        gpu = None
    return {
        "model": MODEL,
        "revision": REVISION,
        "served_name": SERVED_NAME,
        "vllm": vllm,
        "gpu": gpu or GPU,
        "dtype": DTYPE,
        "max_model_len": MAX_MODEL_LEN,
        "deploy_commit": DEPLOY_COMMIT,
    }
