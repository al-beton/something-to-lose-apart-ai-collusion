# Implements: backends/modal
"""vLLM middleware: every route needs the token, not just `/v1`.

vLLM's own `--api-key` guards only `/v1/...`; its other inference routes
(`/invocations`, `/inference/v1/generate`, ...) answer anyone, and it logs
its arguments, key included. `deploy/modal_vllm.py` loads this with
`--middleware vllm_token.require_token` instead: a request needs
`Authorization: Bearer $VLLM_API_KEY` (from the Modal secret, never a command
line) unless it is a health check.
"""

import hmac
import os

OPEN = {"/health", "/ping"}  # readiness checks, which serve no model output


async def require_token(request, call_next):
    if request.url.path not in OPEN:
        expected = f"Bearer {os.environ['VLLM_API_KEY']}".encode()
        given = request.headers.get("authorization", "").encode()
        if not hmac.compare_digest(given, expected):
            from starlette.responses import JSONResponse

            return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return await call_next(request)
