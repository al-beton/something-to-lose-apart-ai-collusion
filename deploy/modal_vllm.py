# Implements: backends/modal
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
- Auth: Modal lets requests through (`unauthenticated=True`), and vLLM
  refuses any without the token in the Modal secret `collusion-lab-vllm`
  (`VLLM_API_KEY`); the lab sends it from the variable its agent's
  `api_key_env` names. The token never goes in a config.
- Cost: billed by GPU time while a container is up. One starts on the first
  request (a few minutes to load the weights; the first deploy also
  downloads them to a Volume) and stops after `scaledown_window` without
  requests, so an idle deployment costs nothing.
- `target_concurrency`: how many requests one container takes before Modal
  starts another; the lab sends up to `concurrency` games times their firms.
"""

import os
import subprocess

import modal

MODEL = os.environ.get("MODEL", "mistralai/Mistral-Small-3.2-24B-Instruct-2506")
SERVED_NAME = os.environ.get("SERVED_NAME", "mistral-small-3.2")
GPU = os.environ.get("GPU", "H100")
MINUTES = 60
PORT = 8000

image = (
    modal.Image.from_registry("nvidia/cuda:12.9.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install("vllm==0.21.0")
    .env({"HF_XET_HIGH_PERFORMANCE": "1", "MODEL": MODEL, "SERVED_NAME": SERVED_NAME})
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
    unauthenticated=True,  # vLLM's --api-key guards it instead
)
class Server:
    @modal.enter()
    def start(self):
        command = [
            "vllm",
            "serve",
            MODEL,
            "--served-model-name",
            SERVED_NAME,
            "--host",
            "0.0.0.0",
            "--port",
            str(PORT),
            "--api-key",
            os.environ["VLLM_API_KEY"],
            "--max-model-len",
            "16384",
        ]
        if MODEL.startswith("mistralai/"):
            # Mistral's own tokenizer and weight format, as its model card asks.
            command += ["--tokenizer-mode", "mistral", "--config-format", "mistral"]
            command += ["--load-format", "mistral"]
        self.process = subprocess.Popen(command)

    @modal.exit()
    def stop(self):
        self.process.terminate()
