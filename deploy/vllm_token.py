# Implements: backends/modal, backends/modal-pinned
"""vLLM middleware: every route needs the token, not just `/v1`.

vLLM's own `--api-key` guards only `/v1/...`; its other inference routes
(`/invocations`, `/inference/v1/generate`, ...) answer anyone, and it logs
its arguments, key included. `deploy/modal_vllm.py` loads this with
`--middleware vllm_token.require_token` instead: a request needs
`Authorization: Bearer $VLLM_API_KEY` (from the Modal secret, never a command
line) unless it is a health check. With the token, `GET /provenance`
answers what the container serves (written at start-up by modal_vllm.py).
"""

import hmac
import json
import os
from pathlib import Path

OPEN = {"/health", "/ping"}  # readiness checks, which serve no model output


async def require_token(request, call_next):
    if request.url.path not in OPEN:
        expected = f"Bearer {os.environ['VLLM_API_KEY']}".encode()
        given = request.headers.get("authorization", "").encode()
        if not hmac.compare_digest(given, expected):
            from starlette.responses import JSONResponse

            return JSONResponse({"error": "Unauthorized"}, status_code=401)
    if request.url.path == "/provenance":
        from starlette.responses import JSONResponse

        path = Path(os.environ.get("PROVENANCE_FILE", "/root/provenance.json"))
        return JSONResponse(json.loads(path.read_text()), status_code=200)
    return await call_next(request)
