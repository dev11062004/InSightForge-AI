"""AI Strategy & Innovation Consultant Agent"""
import groq_patch       # noqa: F401
import rate_limit_retry # noqa: F401

import os
from crewai import Agent, LLM
from test_mode import (
    TEST_MODE, get_model, get_max_tokens, get_max_iter,
    PROD_STRATEGY_MODEL, PROD_MAX_TOKENS_LARGE,
)

llm = LLM(
    model=os.getenv("AI_STRATEGY_AGENT_LLM", get_model(PROD_STRATEGY_MODEL)),
    temperature=float(os.getenv("AI_STRATEGY_AGENT_TEMPERATURE", "0.3")),
    max_tokens=get_max_tokens(PROD_MAX_TOKENS_LARGE),
)

_goal_test = (
    "Read the analysis and return 3 bullet points about AI solutions. "
    "Be extremely brief."
)
_goal_prod = (
    "For the top 6 business challenges identified by the analyst, design a "
    "concrete, company-specific AI opportunity. Each recommendation must include: "
    "AI Opportunity, Recommended Solution, Technologies Required, Estimated ROI, "
    "and Business Impact. Be specific and concise — no repetition of prior context."
)

_backstory_test = "You are a strategist. Return only short bullet points. No explanations."
_backstory_prod = (
    "You are a Principal AI Strategist who has architected AI transformation "
    "roadmaps for 50+ large enterprises. You have deep hands-on experience "
    "deploying LLMs, computer vision, and predictive analytics. "
    "You NEVER recommend generic solutions. You ground every recommendation in "
    "the specific company's context. You write concisely for executive audiences."
)

ai_strategy_agent = Agent(
    role="AI Strategy Consultant",
    goal=_goal_test if TEST_MODE else _goal_prod,
    backstory=_backstory_test if TEST_MODE else _backstory_prod,
    llm=llm,
    tools=[],
    verbose=True,
    memory=False,
    max_iter=get_max_iter(),
    max_retry_limit=2,
    allow_delegation=False,
)
