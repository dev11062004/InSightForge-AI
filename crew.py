"""
crew.py — AI Company Intelligence System
Assembles the 4-agent sequential pipeline.

IMPORTANT: groq_patch is imported inside each agent module (which are imported
here), so the litellm monkey-patch is always applied before any LLM call.
"""

import groq_patch  # noqa: F401  — ensure patch is active even if imported standalone

from crewai import Crew, Process

from agents.research_specialist import research_specialist_agent
from agents.data_analyst import data_analyst_agent
from agents.ai_strategy_agent import ai_strategy_agent
from agents.content_writer import content_writer_agent

from tasks.research_task import research_task
from tasks.analysis_task import analysis_task
from tasks.ai_strategy_task import ai_strategy_task
from tasks.writing_task import writing_task


intelligence_crew = Crew(
    agents=[
        research_specialist_agent,
        data_analyst_agent,
        ai_strategy_agent,
        content_writer_agent,
    ],
    tasks=[
        research_task,
        analysis_task,
        ai_strategy_task,
        writing_task,
    ],
    process=Process.sequential,
    # memory=False: Crew memory requires an embedding model (OpenAI by default).
    # Enabling it without configuring embedder causes a second API error.
    # Per-agent context is passed via task.context=[...] instead.
    memory=False,
    verbose=True,
)