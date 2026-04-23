import hashlib
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.session_manager import session_manager

_HOP_BY_HOP_AND_ENTITY = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-length",
        "content-encoding",
    }
)


def _dedup_post_paths() -> frozenset[str]:
    base = settings.API_V1_STR.rstrip("/")
    return frozenset(
        {
            f"{base}/move",
            f"{base}/deal",
            f"{base}/undo",
            f"{base}/solve",
        }
    )


class RequestDedupMiddleware(BaseHTTPMiddleware):
    """
    Per-session serialization plus replay of identical mutating POSTs when the
    board revision (historycount) has not advanced since the last response.
    Mitigates duplicate clicks delivered over latent networks.
    """

    async def dispatch(self, request: Request, call_next):
        if not settings.ENABLE_REQUEST_DEDUP or request.method != "POST":
            return await call_next(request)

        path = request.url.path
        if path not in _dedup_post_paths():
            return await call_next(request)

        body = await request.body()

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request = Request(request.scope, receive=receive)

        session_id = getattr(request.state, "session_id", None)
        if not session_id:
            return await call_next(request)

        game = session_manager.get_session(session_id)
        if game is None:
            return await call_next(request)

        sig = hashlib.sha256(path.encode("utf-8") + b"\0" + body).hexdigest()

        lock = session_manager.get_request_lock(session_id)
        async with lock:
            pre_token = int(game.historycount)

            cached = session_manager.get_dedup_cache(session_id)
            if cached:
                age = time.monotonic() - cached["ts_mono"]
                if (
                    cached["sig"] == sig
                    and int(cached["post_token"]) == pre_token
                    and age < settings.DEDUP_WINDOW_SECONDS
                ):
                    hdrs = {
                        k: v
                        for k, v in cached["headers"].items()
                        if k.lower() not in _HOP_BY_HOP_AND_ENTITY
                    }
                    hdrs["X-Request-Dedup"] = "replay"
                    return Response(
                        content=cached["body"],
                        status_code=cached["status_code"],
                        headers=hdrs,
                        media_type=cached.get("media_type") or "application/json",
                    )

            response = await call_next(request)

            parts: list[bytes] = []
            async for chunk in response.body_iterator:
                parts.append(chunk)
            payload = b"".join(parts)

            if response.status_code >= 500:
                return Response(
                    content=payload,
                    status_code=response.status_code,
                    headers={
                        k: v
                        for k, v in response.headers.items()
                        if k.lower() not in _HOP_BY_HOP_AND_ENTITY
                    },
                    media_type=response.media_type,
                )

            post_token = int(game.historycount)
            stable_headers = {
                k: v
                for k, v in response.headers.items()
                if k.lower() not in _HOP_BY_HOP_AND_ENTITY
            }
            media_type = response.media_type
            if media_type is None:
                media_type = response.headers.get("content-type", "application/json")

            session_manager.set_dedup_cache(
                session_id,
                {
                    "sig": sig,
                    "post_token": post_token,
                    "body": payload,
                    "status_code": response.status_code,
                    "headers": stable_headers,
                    "media_type": media_type,
                    "ts_mono": time.monotonic(),
                },
            )

            return Response(
                content=payload,
                status_code=response.status_code,
                headers={
                    k: v
                    for k, v in response.headers.items()
                    if k.lower() not in _HOP_BY_HOP_AND_ENTITY
                },
                media_type=response.media_type,
            )
