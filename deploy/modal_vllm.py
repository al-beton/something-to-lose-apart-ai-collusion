# Implements: backends/modal, backends/modal-pinned, backends/modal-any-model
"""An open model on Modal, behind vLLM's OpenAI-compatible server.

    uvx modal deploy deploy/modal_vllm.py

prints the address it serves at (of the form
`https://<workspace>--collusion-lab-vllm-server.us-east.modal.direct`); a
config reaches it as `api_base: <address>/v1` with `model: openai/<SERVED_NAME>`
(see `configs/modal.yaml`). Any other open model that fits on one or two H100s
deploys the same way as its own app, beside this one, from the environment
alone:

    APP_NAME=collusion-lab-gemma MODEL=google/gemma-4-31B-it \
      SERVED_NAME=gemma-4-31b-it REVISION=<commit> HF_SECRET=huggingface \
      uvx modal deploy deploy/modal_vllm.py

`APP_NAME` names the app (default `collusion-lab-vllm`, Mistral's), `MODEL`
and `REVISION` the Hugging Face model and commit, `SERVED_NAME` the name a
config asks for, `GPU` and `GPUS` the card and how many (two spreads the
model over both), and `TEXT_ONLY=1` serves a model that also reads images
(Gemma 4) for text alone. `VLLM` picks the vLLM release (default 0.21.0,
Mistral's); Gemma 4 needs 0.32.0, whose Transformers knows it. They are baked into the image, so the container serves what
you deployed. Shaped on Modal's own vLLM
example (docs/examples/vllm_inference).

- Model: Mistral Small 3.2 (24B), the model the lab's cheap and stakes
  configs use through OpenRouter. About 48 GB in bf16, so it fits one H100
  (80 GB) with room for many games at once. A gated model (Llama, say) also
  needs a Hugging Face token: `HF_SECRET=huggingface` attaches the Modal
  secret of that name (holding `HF_TOKEN`), which you create yourself; the
  token reaches the container only through it, never through this script.
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
APP_NAME = os.environ.get("APP_NAME", "collusion-lab-vllm")
GPU = os.environ.get("GPU", "H100")
GPUS = int(os.environ.get("GPUS", "1"))  # more than one: the model is split
HF_SECRET = os.environ.get("HF_SECRET")  # a Modal secret holding HF_TOKEN
TEXT_ONLY = os.environ.get("TEXT_ONLY") == "1"  # a model that also reads images
VLLM = os.environ.get("VLLM", "0.21.0")  # newer models need newer vLLM
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
    .uv_pip_install(f"vllm=={VLLM}")
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
            "GPUS": str(GPUS),
            "TEXT_ONLY": "1" if TEXT_ONLY else "",
            "APP_NAME": APP_NAME,
            "PYTHONPATH": "/root",  # so vLLM can import vllm_token
        }
    )
    .add_local_file(Path(__file__).with_name("vllm_token.py"), "/root/vllm_token.py")
)
weights = modal.Volume.from_name("collusion-lab-hf-cache", create_if_missing=True)
compiled = modal.Volume.from_name("collusion-lab-vllm-cache", create_if_missing=True)

app = modal.App(APP_NAME)
secrets = [modal.Secret.from_name("collusion-lab-vllm")]
if HF_SECRET:
    secrets.append(modal.Secret.from_name(HF_SECRET))


@app.function(
    image=image,
    volumes={"/root/.cache/huggingface": weights},
    secrets=secrets,
    timeout=60 * MINUTES,
)
def download():
    """Fetch the pinned revision into the weights volume on a CPU, so the GPU
    server never waits on a download: `uvx modal run
    deploy/modal_vllm.py::download`, with the same settings, before a new
    model's first deploy."""
    from huggingface_hub import snapshot_download

    path = snapshot_download(MODEL, revision=REVISION)
    weights.commit()
    print(f"{MODEL}@{REVISION}:", ", ".join(sorted(os.listdir(path))))


@app.server(
    image=image,
    gpu=f"{GPU}:{GPUS}" if GPUS > 1 else GPU,
    scaledown_window=5 * MINUTES,
    startup_timeout=20 * MINUTES,
    volumes={"/root/.cache/huggingface": weights, "/root/.cache/vllm": compiled},
    secrets=secrets,
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
        if GPUS > 1:
            command += ["--tensor-parallel-size", str(GPUS)]
        if TEXT_ONLY:  # no image encoder memory for a game that sends none
            command += ["--limit-mm-per-prompt", json.dumps({"image": 0})]
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
