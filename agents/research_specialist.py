"""Research Specialist Agent — Corporate Intelligence Gatherer"""
import groq_patch       # noqa: F401  — must be first, patches litellm
import rate_limit_retry # noqa: F401  — adds retry-with-backoff on RateLimitError

import os
from crewai import Agent, LLM
from crewai_tools import SerperDevTool
from test_mode import (
    TEST_MODE, get_model, get_max_tokens, get_max_iter,
    PROD_RESEARCH_MODEL, PROD_MAX_TOKENS_SMALL,
)

llm = LLM(
    model=os.getenv("RESEARCH_AGENT_LLM", get_model(PROD_RESEARCH_MODEL)),
    temperature=float(os.getenv("RESEARCH_AGENT_TEMPERATURE", "0.1")),
    max_tokens=get_max_tokens(PROD_MAX_TOKENS_SMALL),
)

_goal_test = (
    "Search for basic facts about the company and return 3 bullet points. "
    "Be as brief as possible."
)
_goal_prod = (
    "Conduct focused, multi-source research on a given company and produce a "
    "concise intelligence dossier covering its business: overview, financials, "
    "leadership, recent news, and key partnerships. "
    "Every factual claim must be attributed to a verifiable source."
)

_backstory_test = "You are a researcher. Return only short bullet points. No explanations."
_backstory_prod = (
    "You are a former McKinsey research analyst with 15 years of experience in "
    "corporate intelligence gathering. You extract structured, evidence-backed insights "
    "from public filings, news archives, and press releases. "
    "You are rigorous and methodical. You write concisely — no padding, no repetition."
)

research_specialist_agent = Agent(
    role="Corporate Intelligence Researcher",
    goal=_goal_test if TEST_MODE else _goal_prod,
    backstory=_backstory_test if TEST_MODE else _backstory_prod,
    llm=llm,
    tools=[SerperDevTool()],
    verbose=True,
    memory=False,
    max_iter=get_max_iter(),
    max_retry_limit=2,
    allow_delegation=False,
)
