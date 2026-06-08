"""Data / Business Intelligence Analyst Agent"""
import groq_patch       # noqa: F401
import rate_limit_retry # noqa: F401

import os
from crewai import Agent, LLM
from crewai_tools import FileReadTool
from test_mode import (
    TEST_MODE, get_model, get_max_tokens, get_max_iter,
    PROD_ANALYST_MODEL, PROD_MAX_TOKENS_SMALL,
)

llm = LLM(
    model=os.getenv("ANALYST_AGENT_LLM", get_model(PROD_ANALYST_MODEL)),
    temperature=float(os.getenv("ANALYST_AGENT_TEMPERATURE", "0.2")),
    max_tokens=get_max_tokens(PROD_MAX_TOKENS_SMALL),
)

_goal_test = (
    "Read the research and return 3 bullet points about the company's challenges. "
    "Be extremely brief."
)
_goal_prod = (
    "Analyze the research dossier on a company and produce a concise Business "
    "Intelligence report. Identify the top revenue drivers, customer segments, "
    "and competitive position. Identify 6-8 key challenges with evidence and "
    "Confidence Scores. Be specific but concise — no padding."
)

_backstory_test = "You are an analyst. Return only short bullet points. No explanations."
_backstory_prod = (
    "You are a veteran Management Consultant with a background at BCG and Deloitte. "
    "You translate raw research into structured insights using Porter's Five Forces "
    "and SWOT frameworks. Every claim is supported by data. You write concisely "
    "for senior stakeholders who value brevity and precision over volume."
)

data_analyst_agent = Agent(
    role="Business Intelligence Analyst",
    goal=_goal_test if TEST_MODE else _goal_prod,
    backstory=_backstory_test if TEST_MODE else _backstory_prod,
    llm=llm,
    tools=[FileReadTool()],
    verbose=True,
    memory=False,
    max_iter=get_max_iter(),
    max_retry_limit=2,
    allow_delegation=False,
)
