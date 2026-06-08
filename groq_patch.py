"""
groq_patch.py — Must be imported BEFORE crewai or litellm are used.

Root cause of the cache_breakpoint error:
  CrewAI 1.14.6 marks messages with {"cache_breakpoint": True} for Anthropic
  prompt caching. For native Anthropic provider this is stripped correctly.
  For the LiteLLM path (used for groq/ models), _prepare_completion_params
  calls _format_messages_for_provider which does NOT strip cache_breakpoint,
  so the raw key reaches litellm.completion() → Groq API → rejection.

Fix strategy:
  1. Wrap litellm.completion and litellm.acompletion to strip cache_breakpoint
     from every message before the HTTP call is made.
  2. Set litellm.drop_params = True so any other stray Anthropic params
     (cache_control, etc.) are silently dropped.
  3. Set the LITELLM_DROP_PARAMS env var as a belt-and-suspenders backup.
"""

from __future__ import annotations

import os
import sys
import logging

# ── Fix Windows console encoding (cp1252 chokes on CrewAI emoji logs) ─────────
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # non-fatal: if reconfigure fails, emoji chars will just be replaced

# ── Belt-and-suspenders env var ───────────────────────────────────────────────
os.environ.setdefault("LITELLM_DROP_PARAMS", "true")
os.environ.setdefault("LITELLM_LOG", "ERROR")    # suppress litellm verbose logs

logger = logging.getLogger(__name__)

# Keys that Groq (and other non-Anthropic providers) reject
_UNSUPPORTED_MSG_KEYS = frozenset({
    "cache_breakpoint",
    "cache_control",
})


def _clean_messages(messages: list | None) -> list | None:
    """Remove Anthropic-specific keys from every message dict."""
    if not isinstance(messages, list):
        return messages
    cleaned = []
    for msg in messages:
        if isinstance(msg, dict) and _UNSUPPORTED_MSG_KEYS.intersection(msg):
            msg = {k: v for k, v in msg.items() if k not in _UNSUPPORTED_MSG_KEYS}
        cleaned.append(msg)
    return cleaned


def _patch_litellm() -> None:
    """Monkey-patch litellm.completion and litellm.acompletion."""
    try:
        import litellm as _ll

        # Global flag — also set programmatically in case env var is ignored
        _ll.drop_params = True

        # ── Sync completion ───────────────────────────────────────────────────
        _orig_completion = _ll.completion

        def _patched_completion(*args, **kwargs):  # type: ignore[no-untyped-def]
            if "messages" in kwargs:
                kwargs["messages"] = _clean_messages(kwargs["messages"])
            elif args:
                # positional: completion(model, messages, ...)
                lst = list(args)
                if len(lst) >= 2 and isinstance(lst[1], list):
                    lst[1] = _clean_messages(lst[1])
                    args = tuple(lst)
            return _orig_completion(*args, **kwargs)

        _ll.completion = _patched_completion

        # ── Async completion ──────────────────────────────────────────────────
        _orig_acompletion = _ll.acompletion

        async def _patched_acompletion(*args, **kwargs):  # type: ignore[no-untyped-def]
            if "messages" in kwargs:
                kwargs["messages"] = _clean_messages(kwargs["messages"])
            elif args:
                lst = list(args)
                if len(lst) >= 2 and isinstance(lst[1], list):
                    lst[1] = _clean_messages(lst[1])
                    args = tuple(lst)
            return await _orig_acompletion(*args, **kwargs)

        _ll.acompletion = _patched_acompletion

        logger.info("groq_patch: litellm.completion patched — cache_breakpoint stripping active")

    except ImportError:
        logger.warning("groq_patch: litellm not installed — patch skipped")


_patch_litellm()
