"""
test_mode.py — Global TEST_MODE flag and shared lightweight config.

Set TEST_MODE = True to run the full CrewAI pipeline end-to-end with
ultra-minimal token usage, allowing verification on Groq's free tier
without hitting the 12,000 TPM rate limit.

Set TEST_MODE = False to restore normal production prompts.

All agents and tasks import from this module so there is exactly ONE
place to flip the switch.
"""

import os

# ── Master switch ─────────────────────────────────────────────────────────────
# Override via environment variable so you can also flip it without code changes:
#   set TEST_MODE=true   (Windows)
#   export TEST_MODE=true (Linux/Mac)
TEST_MODE: bool = os.getenv("TEST_MODE", "true").lower() in ("1", "true", "yes")

# ── Model config ──────────────────────────────────────────────────────────────
# llama-3.1-8b-instant: smallest/fastest Groq model, ~30k TPM on free tier
# vs llama-3.3-70b-versatile which is capped at 12k TPM.
TEST_MODEL  = "groq/llama-3.1-8b-instant"
PROD_RESEARCH_MODEL  = "groq/llama-3.1-8b-instant"
PROD_ANALYST_MODEL   = "groq/llama-3.1-8b-instant"
PROD_STRATEGY_MODEL  = "groq/llama-3.3-70b-versatile"
PROD_WRITER_MODEL    = "groq/llama-3.3-70b-versatile"

# ── Token limits ──────────────────────────────────────────────────────────────
TEST_MAX_TOKENS = 300    # each agent output ≤ 300 tokens (~200 words)
PROD_MAX_TOKENS_SMALL = 2048
PROD_MAX_TOKENS_LARGE = 4096

# ── Iteration limits ──────────────────────────────────────────────────────────
TEST_MAX_ITER = 2    # CrewAI needs ≥2: one tool/think step + one final-answer step
PROD_MAX_ITER = 3


def get_model(prod_model: str) -> str:
    return TEST_MODEL if TEST_MODE else prod_model


def get_max_tokens(prod_tokens: int) -> int:
    return TEST_MAX_TOKENS if TEST_MODE else prod_tokens


def get_max_iter() -> int:
    return TEST_MAX_ITER if TEST_MODE else PROD_MAX_ITER
