"""
PropIQ SSE streaming helper.

Wraps an async generator of dict/str events into a `text/event-stream` response.
Uses sse-starlette when installed (proper SSE framing, keep-alive); otherwise a
hand-rolled StreamingResponse yielding `data: {...}\\n\\n`. Either way the client
consumes it with a standard EventSource — no new server or protocol.
"""

from __future__ import annotations

import json
from typing import AsyncIterator


def _format_event(payload) -> str:
    if isinstance(payload, (dict, list)):
        payload = json.dumps(payload)
    return f"data: {payload}\n\n"


def sse_response(generator: AsyncIterator):
    """Return a FastAPI-compatible SSE response from an async generator."""
    try:
        from sse_starlette.sse import EventSourceResponse

        async def _wrap():
            async for item in generator:
                if isinstance(item, (dict, list)):
                    yield {"data": json.dumps(item)}
                else:
                    yield {"data": str(item)}

        return EventSourceResponse(_wrap())
    except Exception:
        from fastapi.responses import StreamingResponse

        async def _hand_rolled():
            async for item in generator:
                yield _format_event(item)

        return StreamingResponse(_hand_rolled(), media_type="text/event-stream")
