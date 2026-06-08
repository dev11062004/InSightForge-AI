"""
rate_limit_retry.py — Automatic retry + exponential backoff for Groq TPM limits.

Must be imported AFTER groq_patch (which is already guaranteed by app.py / main.py
importing groq_patch first).

Strategy
--------
1. Wrap litellm.completion / litellm.acompletion with a retry loop.
2. On RateLimitError, parse the "retry in X seconds" hint from the error body.
3. Wait (with optional Streamlit progress feedback), then retry.
4. Use exponential backoff when no hint is available.
5. Give up after MAX_RETRIES and re-raise so the caller can show a clean UI error.
"""

from __future__ import annotations

import re
import time
import logging
import asyncio
from typing import Callable, Any

logger = logging.getLogger(__name__)

# ── Tunables ──────────────────────────────────────────────────────────────────
MAX_RETRIES       = 5          # total attempts before giving up
BASE_BACKOFF_SEC  = 15         # minimum wait when no hint in error body
MAX_BACKOFF_SEC   = 120        # cap for exponential backoff
BACKOFF_MULTIPLIER = 2.0       # each retry doubles the wait


def _parse_retry_after(error_str: str) -> float | None:
    """Extract 'Please try again in X.Xs' from Groq's error message."""
    match = re.search(
        r"[Pp]lease try again in\s+([\d.]+)\s*s",
        error_str,
    )
    if match:
        return float(match.group(1)) + 1.0   # add 1 s buffer
    return None


def _wait_with_log(seconds: float, attempt: int) -> None:
    """Sleep and emit a log every 5 s so the user knows we're alive."""
    logger.warning(
        "Groq rate limit hit (attempt %d/%d). Waiting %.0f s before retry...",
        attempt, MAX_RETRIES, seconds,
    )
    remaining = seconds
    while remaining > 0:
        chunk = min(5.0, remaining)
        time.sleep(chunk)
        remaining -= chunk
        if remaining > 0:
            logger.info("  ...still waiting %.0f s more...", remaining)


async def _async_wait_with_log(seconds: float, attempt: int) -> None:
    logger.warning(
        "Groq rate limit hit (attempt %d/%d). Waiting %.0f s before retry...",
        attempt, MAX_RETRIES, seconds,
    )
    await asyncio.sleep(seconds)


# ── Core patch ────────────────────────────────────────────────────────────────

def _patch_retry() -> None:
    """Add retry-with-backoff around litellm.completion and .acompletion."""
    try:
        import litellm as _ll
        from litellm.exceptions import RateLimitError  # type: ignore[import]

        # --- sync ---
        _orig_completion = _ll.completion

        def _retrying_completion(*args: Any, **kwargs: Any) -> Any:
            backoff = BASE_BACKOFF_SEC
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    return _orig_completion(*args, **kwargs)
                except RateLimitError as exc:
                    if attempt == MAX_RETRIES:
                        logger.error("All %d retry attempts exhausted. Raising.", MAX_RETRIES)
                        raise
                    hint = _parse_retry_after(str(exc))
                    wait = hint if hint else min(backoff, MAX_BACKOFF_SEC)
                    _wait_with_log(wait, attempt)
                    backoff = min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF_SEC)

        _ll.completion = _retrying_completion

        # --- async ---
        _orig_acompletion = _ll.acompletion

        async def _retrying_acompletion(*args: Any, **kwargs: Any) -> Any:
            backoff = BASE_BACKOFF_SEC
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    return await _orig_acompletion(*args, **kwargs)
                except RateLimitError as exc:
                    if attempt == MAX_RETRIES:
                        raise
                    hint = _parse_retry_after(str(exc))
                    wait = hint if hint else min(backoff, MAX_BACKOFF_SEC)
                    await _async_wait_with_log(wait, attempt)
                    backoff = min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF_SEC)

        _ll.acompletion = _retrying_acompletion

        logger.info("rate_limit_retry: retry wrapper active (max=%d retries)", MAX_RETRIES)

    except ImportError:
        logger.warning("rate_limit_retry: litellm not installed — retry patch skipped")


_patch_retry()


# ── Streamlit-friendly helper ─────────────────────────────────────────────────

def format_rate_limit_message(exc: Exception) -> str:
    """
    Convert a raw RateLimitError into a clean, user-facing message.
    Called from the Streamlit except block.
    """
    raw = str(exc)
    wait = _parse_retry_after(raw)
    if wait:
        return (
            f"⚠️ Groq rate limit reached. The system waited {wait:.0f}s and retried "
            f"automatically but still hit the limit.\n\n"
            f"**Please wait ~60 seconds and try again**, or upgrade your Groq plan at "
            f"https://console.groq.com/settings/billing"
        )
    return (
        "⚠️ **Groq API rate limit exceeded.**\n\n"
        "The pipeline uses multiple large agents that together exceed the free-tier "
        "12,000 tokens-per-minute limit.\n\n"
        "**Options:**\n"
        "- Wait 60 seconds and try again\n"
        "- Upgrade to Groq Dev Tier at https://console.groq.com/settings/billing\n"
        "- Use a shorter company name or one with less public data"
    )
