"""Executive Communications and Strategy Writer Agent"""
import groq_patch       # noqa: F401
import rate_limit_retry # noqa: F401

import os
from crewai import Agent, LLM
from crewai_tools import FileWriterTool
from test_mode import (
    TEST_MODE, get_model, get_max_tokens, get_max_iter,
    PROD_WRITER_MODEL, PROD_MAX_TOKENS_LARGE,
)

llm = LLM(
    model=os.getenv("WRITER_AGENT_LLM", get_model(PROD_WRITER_MODEL)),
    temperature=float(os.getenv("WRITER_AGENT_TEMPERATURE", "0.4")),
    max_tokens=get_max_tokens(PROD_MAX_TOKENS_LARGE),
)

_goal_test = (
    "Write a minimal report with 3 bullet points per section. "
    "Save final_report.md and ceo_pitch.md using FileWriterTool. "
    "Keep each file under 150 words."
)
_goal_prod = (
    "Synthesize all research, analysis, and AI strategy into two concise outputs: "
    "(1) A structured Business Intelligence Report in professional markdown with "
    "all required sections. "
    "(2) A personalized one-page CEO Consulting Pitch. "
    "Be thorough but concise — target 1500-2000 words for the report. "
    "Do NOT repeat content already written by prior agents — synthesise and add narrative."
)

_backstory_test = "You are a writer. Write minimal bullet-point summaries. Save the files."
_backstory_prod = (
    "You are a Senior Partner at a top-tier management consulting firm with 20 years "
    "of experience writing board-level presentations for India's largest conglomerates. "
    "Your writing is precise, professional, and structured — never verbose. "
    "You synthesise complex inputs into crisp executive narratives. "
    "You always produce complete, well-formatted markdown with proper headings."
)

content_writer_agent = Agent(
    role="Executive Writer",
    goal=_goal_test if TEST_MODE else _goal_prod,
    backstory=_backstory_test if TEST_MODE else _backstory_prod,
    llm=llm,
    tools=[FileWriterTool()],
    verbose=True,
    memory=False,
    max_iter=get_max_iter(),
    max_retry_limit=2,
    allow_delegation=False,
)
