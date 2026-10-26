<!-- Implements: specs-and-docs/folder-guides -->
# Deploy

Serving an open model on our own GPUs on [Modal](https://modal.com), behind vLLM's OpenAI-compatible server.

- **`modal_vllm.py`:** one command deploys a model as its own app (Mistral Small 3.2 by default, Gemma 4 31B and others by setting the environment). Its docstring has every setting.
- **`vllm_token.py`:** refuses every request without the token, except health checks.

The steps, from sign-in to tear-down, are in the top-level README's "Running on Modal".
