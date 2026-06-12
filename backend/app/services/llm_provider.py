"""
PropIQ LLM Provider — one pluggable entry point for all LLM calls.

Today this dispatches to Groq (the only configured provider), but every caller
goes through `chat()` / `chat_stream()` / `chat_tools()` so swapping or adding a
provider later is a one-file change. Models:
  - tier "fast"   -> llama-3.1-8b-instant   (extraction, cheap classification)
  - tier "reason" -> llama-3.3-70b-versatile (memos, agent planning, verification)

GRACEFUL DEGRADATION: if `groq` is not installed or GROQ_API_KEY is missing,
`is_available()` returns False and callers fall back to their deterministic
paths. No LLM call ever raises into a request.
"""

from __future__ import annotations

import json
import logging
import os
from typing import AsyncIterator, Dict, List, Optional

logger = logging.getLogger(__name__)

_MODELS = {
    "fast": "llama-3.1-8b-instant",
    "reason": "llama-3.3-70b-versatile",
}


def _api_key() -> str:
    return os.getenv("GROQ_API_KEY", "")


def is_available() -> bool:
    """True only if the provider can actually serve a request."""
    if not _api_key():
        return False
    try:
        import groq  # noqa: F401

        return True
    except Exception:
        return False


def model_for(tier: str) -> str:
    return _MODELS.get(tier, _MODELS["reason"])


async def chat(
    messages: List[Dict],
    model_tier: str = "reason",
    temperature: float = 0.3,
    max_tokens: int = 600,
    response_format: Optional[Dict] = None,
) -> Dict:
    """
    Plain chat completion. Returns {"text": str, "ok": bool}. Never raises.
    """
    if not is_available():
        return {"text": "", "ok": False, "reason": "llm_unavailable"}
    try:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=_api_key())
        kwargs = dict(
            model=model_for(model_tier),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if response_format:
            kwargs["response_format"] = response_format
        completion = await client.chat.completions.create(**kwargs)
        return {"text": completion.choices[0].message.content.strip(), "ok": True}
    except Exception as e:
        logger.warning("LLM chat failed: %s", e)
        return {"text": "", "ok": False, "reason": str(e)[:200]}


async def chat_json(
    messages: List[Dict], model_tier: str = "reason", max_tokens: int = 600
) -> Optional[Dict]:
    """Chat that must return valid JSON. Returns parsed dict or None."""
    res = await chat(
        messages,
        model_tier=model_tier,
        temperature=0.1,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    if not res["ok"]:
        return None
    try:
        return json.loads(res["text"])
    except Exception:
        return None


async def chat_tools(
    messages: List[Dict],
    tools: List[Dict],
    model_tier: str = "reason",
    temperature: float = 0.2,
    max_tokens: int = 800,
) -> Dict:
    """
    Tool-calling completion. Returns:
      {"ok": bool, "stop_reason": "tool_use"|"end"|..., "text": str,
       "tool_calls": [{"id","name","arguments"}]}
    Mirrors the shape the agent loop expects regardless of provider.
    """
    if not is_available():
        return {"ok": False, "stop_reason": "unavailable", "text": "", "tool_calls": []}
    try:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=_api_key())
        completion = await client.chat.completions.create(
            model=model_for(model_tier),
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = completion.choices[0]
        msg = choice.message
        tool_calls = []
        for tc in (msg.tool_calls or []):
            try:
                args = json.loads(tc.function.arguments)
            except Exception:
                args = {}
            tool_calls.append(
                {"id": tc.id, "name": tc.function.name, "arguments": args}
            )
        stop_reason = "tool_use" if tool_calls else "end"
        return {
            "ok": True,
            "stop_reason": stop_reason,
            "text": (msg.content or "").strip(),
            "tool_calls": tool_calls,
            "raw_message": {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in (msg.tool_calls or [])
                ],
            },
        }
    except Exception as e:
        logger.warning("LLM tool-call failed: %s", e)
        return {"ok": False, "stop_reason": "error", "text": "", "tool_calls": [],
                "reason": str(e)[:200]}


async def chat_stream(
    messages: List[Dict], model_tier: str = "reason",
    temperature: float = 0.3, max_tokens: int = 600,
) -> AsyncIterator[str]:
    """
    Async generator yielding text deltas. If unavailable, yields nothing
    (callers should detect is_available() first and fall back).
    """
    if not is_available():
        return
    try:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=_api_key())
        stream = await client.chat.completions.create(
            model=model_for(model_tier),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        logger.warning("LLM stream failed: %s", e)
        return
